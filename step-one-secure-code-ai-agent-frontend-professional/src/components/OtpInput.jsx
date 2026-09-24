import { useRef } from 'react';

export default function OtpInput({ ariaLabel, disabled, onChange, value }) {
  const refs = useRef([]);
  const digits = Array.from({ length: 6 }, (_, index) => value[index] ?? '');

  const updateAt = (index, nextValue) => {
    const digit = nextValue.replace(/\D/g, '').slice(-1);
    const next = [...digits];
    next[index] = digit;
    const joined = next.join('');
    onChange(joined);

    if (digit && index < 5) {
      refs.current[index + 1]?.focus();
    }
  };

  const onKeyDown = (event, index) => {
    if (event.key === 'Backspace' && !digits[index] && index > 0) {
      refs.current[index - 1]?.focus();
    }
  };

  const onPaste = (event) => {
    const pasted = event.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pasted) return;
    event.preventDefault();
    onChange(pasted);
    refs.current[Math.min(pasted.length, 6) - 1]?.focus();
  };

  return (
    <div aria-label={ariaLabel} className="otp-row" dir="ltr" onPaste={onPaste} role="group">
      {digits.map((digit, index) => (
        <input
          aria-label={`${ariaLabel} ${index + 1}`}
          autoComplete={index === 0 ? 'one-time-code' : 'off'}
          disabled={disabled}
          inputMode="numeric"
          key={index}
          maxLength={1}
          onChange={(event) => updateAt(index, event.target.value)}
          onKeyDown={(event) => onKeyDown(event, index)}
          ref={(node) => {
            refs.current[index] = node;
          }}
          type="text"
          value={digit}
        />
      ))}
    </div>
  );
}
