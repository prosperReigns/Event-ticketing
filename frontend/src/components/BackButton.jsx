import { useNavigate } from "react-router-dom";

const BackButton = ({ className = "" }) => {
  const navigate = useNavigate();

  return (
    <button
      type="button"
      onClick={() => navigate(-1)}
      className={`inline-flex items-center gap-2 text-sm font-semibold text-slate-600 transition hover:text-slate-900 ${className}`}
      aria-label="Go back"
    >
      <span aria-hidden="true">&lt;</span>
      Back
    </button>
  );
};

export default BackButton;
