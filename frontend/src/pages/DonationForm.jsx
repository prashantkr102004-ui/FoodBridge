import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getApiErrorMessage } from "../api/client";
import LocationPicker from "../components/LocationPicker";
import LoadingSpinner from "../components/LoadingSpinner";
import { useAuth } from "../context/AuthContext";
import { donationService } from "../services/donationService";
import { fromLocalDateTimeInput, isValidCoordinatePair, toLocalDateTimeInput } from "../utils/format";
import { getMediaUrl } from "../utils/media";

const initialForm = {
  food_name: "",
  food_type: "VEGETARIAN",
  quantity: "0.5",
  quantity_unit: "KG",
  description: "",
  prepared_at: "",
  available_until: "",
  pickup_address: "",
  latitude: "",
  longitude: "",
  image_url: ""
};

export default function DonationForm({ mode }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(mode === "edit");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraStarting, setCameraStarting] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    if (mode !== "edit") return;
    donationService.detail(id)
      .then((donation) => {
        setForm({
          food_name: donation.food_name || "",
          food_type: donation.food_type || "VEGETARIAN",
          quantity: donation.quantity || "",
          quantity_unit: donation.quantity_unit || "KG",
          description: donation.description || "",
          prepared_at: toLocalDateTimeInput(donation.prepared_at),
          available_until: toLocalDateTimeInput(donation.available_until),
          pickup_address: donation.pickup_address || "",
          latitude: donation.latitude ?? "",
          longitude: donation.longitude ?? "",
          image_url: donation.image_url || ""
        });
      })
      .catch(() => setError("Could not load donation for editing."))
      .finally(() => setLoading(false));
  }, [id, mode]);

  useEffect(() => {
    if (mode !== "create") return;
    setForm((current) => ({
      ...current,
      pickup_address: current.pickup_address || user.location || "",
      latitude: current.latitude || user.latitude || "",
      longitude: current.longitude || user.longitude || ""
    }));
  }, [mode, user.location, user.latitude, user.longitude]);

  useEffect(() => {
    if (cameraOpen && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [cameraOpen]);

  useEffect(() => () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  function validate() {
    if (!form.food_name.trim()) return "Food name is required.";
    if (!form.pickup_address.trim()) return "Pickup address is required.";
    if (Number(form.quantity) <= 0) return "Quantity must be greater than 0.";
    if (!form.prepared_at || !form.available_until) return "Prepared and available-until times are required.";
    if (new Date(form.available_until) <= new Date()) return "Available until must be in the future.";
    if (!isValidCoordinatePair(form.latitude, form.longitude)) return "Enter both valid pickup latitude and longitude, or leave both blank.";
    return "";
  }

  async function uploadImageFile(file) {
    setError("");
    setUploadingImage(true);
    try {
      const data = await donationService.uploadImage(file);
      setForm((current) => ({ ...current, image_url: data.image_url }));
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setUploadingImage(false);
    }
  }

  async function handleImageChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    await uploadImageFile(file);
    event.target.value = "";
  }

  function stopCamera() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraOpen(false);
  }

  async function startCamera() {
    setCameraError("");
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError("Camera is not supported in this browser.");
      return;
    }

    setCameraStarting(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" }
      });
      streamRef.current = stream;
      setCameraOpen(true);
    } catch (err) {
      if (err.name === "NotAllowedError") {
        setCameraError("Camera permission was denied.");
      } else if (err.name === "NotFoundError") {
        setCameraError("No camera was found on this device.");
      } else {
        setCameraError("Could not start the camera.");
      }
    } finally {
      setCameraStarting(false);
    }
  }

  async function capturePhoto() {
    const video = videoRef.current;
    if (!video) {
      setCameraError("Camera preview is not ready yet.");
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const context = canvas.getContext("2d");
    if (!context) {
      setCameraError("Could not capture picture from the camera.");
      return;
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise((resolve) => {
      canvas.toBlob(resolve, "image/jpeg", 0.9);
    });

    if (!blob) {
      setCameraError("Could not capture picture from the camera.");
      return;
    }

    const file = new File([blob], `food-photo-${Date.now()}.jpg`, { type: "image/jpeg" });
    await uploadImageFile(file);
    stopCamera();
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    const payload = {
      ...form,
      quantity: Number(form.quantity),
      prepared_at: fromLocalDateTimeInput(form.prepared_at),
      available_until: fromLocalDateTimeInput(form.available_until),
      latitude: form.latitude === "" ? null : Number(form.latitude),
      longitude: form.longitude === "" ? null : Number(form.longitude),
      image_url: form.image_url.trim() || null
    };

    setError("");
    setSubmitting(true);
    try {
      if (mode === "edit") {
        await donationService.update(id, payload);
      } else {
        await donationService.create(payload);
      }
      navigate("/donor/donations");
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <LoadingSpinner label="Loading donation form" />;

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Donor</p>
          <h1>{mode === "edit" ? "Edit donation" : "Post surplus food"}</h1>
        </div>
      </div>
      <form className="form-panel two-column" onSubmit={handleSubmit} noValidate>
        {error && <p className="alert error span-2">{error}</p>}
        <label>Food name
          <input name="food_name" value={form.food_name} onChange={updateField} required />
        </label>
        <label>Food type
          <select name="food_type" value={form.food_type} onChange={updateField}>
            <option value="VEGETARIAN">VEGETARIAN</option>
            <option value="NON_VEGETARIAN">NON_VEGETARIAN</option>
            <option value="VEGAN">VEGAN</option>
            <option value="OTHER">OTHER</option>
          </select>
        </label>
        <label>Quantity
          <input name="quantity" type="number" min="0.5" step="0.5" value={form.quantity} onChange={updateField} required />
        </label>
        <label>Unit
          <select name="quantity_unit" value={form.quantity_unit} onChange={updateField}>
            <option value="KG">KG</option>
            <option value="MEALS">MEALS</option>
            <option value="PACKETS">PACKETS</option>
            <option value="OTHER">OTHER</option>
          </select>
        </label>
        <label>Prepared at
          <input name="prepared_at" type="datetime-local" value={form.prepared_at} onChange={updateField} required />
        </label>
        <label>Available until
          <input name="available_until" type="datetime-local" value={form.available_until} onChange={updateField} required />
        </label>
        <label className="span-2">Pickup address
          <textarea name="pickup_address" value={form.pickup_address} onChange={updateField} required />
        </label>
        <div className="span-2">
          <LocationPicker
            addressKey="pickup_address"
            onLocation={(coords) => setForm((current) => ({ ...current, ...coords }))}
          />
        </div>
        <label className="span-2">Description
          <textarea name="description" value={form.description} onChange={updateField} />
        </label>
        <div className="span-2 image-upload">
          <span className="field-label">Food picture</span>
          <div className="image-actions">
            <label className="button secondary file-button">
              Add picture
              <input type="file" accept="image/png,image/jpeg,image/webp" onChange={handleImageChange} />
            </label>
            <button className="button secondary" type="button" onClick={startCamera} disabled={cameraStarting || uploadingImage}>
              {cameraStarting ? "Opening camera..." : "Click picture"}
            </button>
          </div>
          {cameraError && <p className="alert error">{cameraError}</p>}
          {cameraOpen && (
            <div className="camera-panel">
              <video ref={videoRef} autoPlay playsInline muted />
              <div className="image-actions">
                <button className="button" type="button" onClick={capturePhoto} disabled={uploadingImage}>
                  Capture photo
                </button>
                <button className="button secondary" type="button" onClick={stopCamera}>
                  Close camera
                </button>
              </div>
            </div>
          )}
          {uploadingImage && <p className="muted">Uploading picture...</p>}
          {form.image_url && (
            <div className="image-preview">
              <img src={getMediaUrl(form.image_url)} alt="Selected food" />
              <button
                className="button secondary"
                type="button"
                onClick={() => setForm((current) => ({ ...current, image_url: "" }))}
              >
                Remove picture
              </button>
            </div>
          )}
        </div>
        <button className="button span-2" disabled={submitting}>{submitting ? "Saving..." : "Save donation"}</button>
      </form>
    </section>
  );
}
