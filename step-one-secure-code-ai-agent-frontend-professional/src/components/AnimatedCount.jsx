import { useEffect, useState } from 'react';

export default function AnimatedCount({ value }) {
  const [displayed, setDisplayed] = useState(() => typeof value === 'number' && !window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : value);

  useEffect(() => {
    if (!Number.isSafeInteger(value) || value < 0 || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setDisplayed(value);
      return undefined;
    }

    let frame;
    const started = performance.now();
    const duration = 550;
    const tick = (now) => {
      const progress = Math.min((now - started) / duration, 1);
      setDisplayed(Math.round(value * (1 - (1 - progress) ** 3)));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value]);

  return displayed;
}
