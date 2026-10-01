// JSX parser fixture. React escapes text content by default; this is not an XSS pack claim.
export function UserLabel({ name }) {
  return <span className="user-label">{name}</span>;
}
