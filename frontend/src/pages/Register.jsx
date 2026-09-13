import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { getApiErrorMessage } from "../api/client";
import { authService } from "../services/authService";
import { getMediaUrl } from "../utils/media";

const receiverRoles = ["NGO", "VOLUNTEER"];
const humanNgoTypes = [
  "Old age home",
  "Orphan children home",
  "Special children home",
  "Community shelter",
  "Other"
];

const initialForm = {
  name: "",
  email: "",
  phone: "",
  password: "",
  role: "DONOR",
  organization_name: "",
  receiver_type: "HUMAN",
  receiver_focus: "Old age home",
  animal_kind: "",
  location: "",
  profile_image_url: ""
};

export default function Register() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const requestedRole = searchParams.get("role");
  const selectedRole = receiverRoles.includes(requestedRole) ? requestedRole : "DONOR";
  const [form, setForm] = useState({ ...initialForm, role: selectedRole });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraStarting, setCameraStarting] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const isReceiver = receiverRoles.includes(form.role);

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
    const { name, value } = event.target;
    setForm((current) => {
      const next = { ...current, [name]: value };
      if (name === "role" && value === "DONOR") {
        next.receiver_type = "HUMAN";
        next.receiver_focus = "Old age home";
        next.animal_kind = "";
        next.profile_image_url = "";
      }
      if (name === "receiver_type") {
        next.receiver_focus = value === "HUMAN" ? "Old age home" : "";
        next.animal_kind = "";
      }
      return next;
    });
  }

  function chooseAccount(role) {
    setForm((current) => ({
      ...current,
      role,
      receiver_type: role === "DONOR" ? "HUMAN" : current.receiver_type,
      receiver_focus: role === "DONOR" ? "Old age home" : current.receiver_focus,
      animal_kind: role === "DONOR" ? "" : current.animal_kind,
      profile_image_url: role === "DONOR" ? "" : current.profile_image_url
    }));
  }

  function validate() {
    if (!form.name.trim()) return "Name is required.";
    if (!form.email.trim()) return "Email is required.";
    if (!form.phone.trim()) return "Contact number is required.";
    if (form.password.length < 8) return "Password must be at least 8 characters.";
    if (!form.location.trim()) return "Address is required.";
    if (isReceiver) {
      if (!form.organization_name.trim()) return "NGO/accepter name is required.";
      if (form.receiver_type === "ANIMAL" && !form.animal_kind.trim()) return "Please enter what kind of animal you support.";
      if (!form.profile_image_url) return "Please add or click a picture of the NGO/accepter.";
    }
    return "";
  }

  async function uploadProfileImage(file) {
    setError("");
    setUploadingImage(true);
    try {
      const data = await authService.uploadReceiverImage(file);
      setForm((current) => ({ ...current, profile_image_url: data.image_url }));
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setUploadingImage(false);
    }
  }

  async function handleImageChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    await uploadProfileImage(file);
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

    const file = new File([blob], `receiver-photo-${Date.now()}.jpg`, { type: "image/jpeg" });
    await uploadProfileImage(file);
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
      name: form.name,
      email: form.email,
      phone: form.phone,
      password: form.password,
      role: form.role,
      organization_name: isReceiver ? form.organization_name : form.organization_name || null,
      receiver_type: isReceiver ? form.receiver_type : null,
      receiver_focus: isReceiver && form.receiver_type === "ANIMAL" ? form.animal_kind : form.receiver_focus,
      profile_image_url: isReceiver ? form.profile_image_url : null,
      location: form.location
    };

    setError("");
    setSubmitting(true);
    try {
      await authService.register(payload);
      navigate("/login", { state: { registered: true } });
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="auth-page wide">
      <div>
        <p className="eyebrow">Join FoodBridge</p>
        <h1>Create your account</h1>
        <p className="muted">Start as a food donor or as an NGO/accepter who receives and distributes food.</p>
      </div>
      <form className="form-panel two-column" onSubmit={handleSubmit}>
        {error && <p className="alert error span-2">{error}</p>}
        <div className="span-2">
          <span className="field-label">Register as</span>
          <div className="account-choice">
            <button className={form.role === "DONOR" ? "active" : ""} type="button" onClick={() => chooseAccount("DONOR")}>
              Donor
            </button>
            <button className={isReceiver ? "active" : ""} type="button" onClick={() => chooseAccount("NGO")}>
              NGO / Accepter
            </button>
          </div>
        </div>
        <label>Your name
          <input name="name" value={form.name} onChange={updateField} required />
        </label>
        <label>Email
          <input name="email" type="email" value={form.email} onChange={updateField} required />
        </label>
        <label>Contact number
          <input name="phone" value={form.phone} onChange={updateField} required />
        </label>
        <label>Password
          <input name="password" type="password" minLength="8" value={form.password} onChange={updateField} required />
        </label>
        {isReceiver && (
          <>
            <label>Receiver role
              <select name="role" value={form.role} onChange={updateField}>
                <option value="NGO">NGO</option>
                <option value="VOLUNTEER">Volunteer accepter</option>
              </select>
            </label>
            <label>Name of NGO/accepter
              <input name="organization_name" value={form.organization_name} onChange={updateField} required />
            </label>
            <label>NGO type
              <select name="receiver_type" value={form.receiver_type} onChange={updateField}>
                <option value="HUMAN">Human support</option>
                <option value="ANIMAL">Animal support</option>
              </select>
            </label>
            {form.receiver_type === "HUMAN" ? (
              <label>Human support category
                <select name="receiver_focus" value={form.receiver_focus} onChange={updateField}>
                  {humanNgoTypes.map((type) => <option key={type} value={type}>{type}</option>)}
                </select>
              </label>
            ) : (
              <label>What kind of animal?
                <input name="animal_kind" value={form.animal_kind} onChange={updateField} placeholder="Dogs, cows, birds..." required />
              </label>
            )}
          </>
        )}
        {!isReceiver && (
          <label className="span-2">Organization name <span className="muted">(optional)</span>
            <input name="organization_name" value={form.organization_name} onChange={updateField} />
          </label>
        )}
        <label className="span-2">Address
          <input name="location" value={form.location} onChange={updateField} required />
        </label>
        {isReceiver && (
          <div className="span-2 image-upload">
            <span className="field-label">NGO/accepter picture</span>
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
            {form.profile_image_url && (
              <div className="image-preview">
                <img src={getMediaUrl(form.profile_image_url)} alt="Selected NGO or accepter" />
                <button className="button secondary" type="button" onClick={() => setForm((current) => ({ ...current, profile_image_url: "" }))}>
                  Remove picture
                </button>
              </div>
            )}
          </div>
        )}
        <button className="button span-2" disabled={submitting || uploadingImage}>{submitting ? "Creating..." : "Create account"}</button>
        <p className="muted span-2">Already registered? <Link to="/login">Login</Link></p>
      </form>
    </section>
  );
}
