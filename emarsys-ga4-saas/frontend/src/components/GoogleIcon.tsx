type GoogleIconProps = {
  className?: string;
};

function GoogleIcon({ className }: GoogleIconProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 533.5 544.3"
      aria-hidden="true"
      focusable="false"
    >
      <path
        fill="#4285F4"
        d="M533.5 278.4c0-17.4-1.6-34.1-4.6-50.2H272v95h146.9c-6.3 34-25 62.7-53.3 81.9v68h86.2c50.3-46.3 81.7-114.6 81.7-194.7z"
      />
      <path
        fill="#34A853"
        d="M272 544.3c72.6 0 133.6-24.1 178.1-65.3l-86.2-68c-24 16.1-54.8 25.6-91.9 25.6-70.7 0-130.6-47.7-152-111.8H32.4v70.3c44.3 87.7 135.4 149.2 239.6 149.2z"
      />
      <path
        fill="#FBBC05"
        d="M120 324.8c-10.4-31-10.4-64.6 0-95.6V158.9H32.4c-37.1 73.6-37.1 161.9 0 235.5l87.6-69.6z"
      />
      <path
        fill="#EA4335"
        d="M272 107.7c39.5-.6 77.4 13.9 106.4 40.9l79.2-79.2C401.4 24.5 337.7-.2 272 0 167.8 0 76.7 61.5 32.4 149.2l87.6 69.6c21.4-64.1 81.3-111.8 152-111.8z"
      />
    </svg>
  );
}

export default GoogleIcon;
