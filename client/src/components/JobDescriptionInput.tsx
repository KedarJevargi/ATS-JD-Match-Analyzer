import { ChangeEvent } from 'react';
import './JobDescriptionInput.css';

interface JobDescriptionInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export const JobDescriptionInput = ({ value, onChange, disabled }: JobDescriptionInputProps) => {
  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  return (
    <div className="jd-input-container">
      <label htmlFor="job-description" className="jd-input-label">
        Job Description
      </label>
      <textarea
        id="job-description"
        className="jd-input-textarea"
        value={value}
        onChange={handleChange}
        disabled={disabled}
        placeholder="Paste the job description here..."
        rows={10}
      />
      <p className="jd-input-hint">
        Include key requirements, skills, and qualifications
      </p>
    </div>
  );
};
