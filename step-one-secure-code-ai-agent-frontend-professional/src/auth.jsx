import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import {
  destroyAuthSession,
  getAuthSession,
  requestEmailChallenge,
  signInWithPassword as passwordSignInRequest,
  verifyEmailChallenge,
} from './api/endpoints';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [pendingEmail, setPendingEmail] = useState('');
  const [challengeId, setChallengeId] = useState('');
  const [emailVerified, setEmailVerified] = useState(true);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(true);
  const [rememberDevice, setRememberDevice] = useState(false);
  const [passwordConfigured, setPasswordConfigured] = useState(false);
  const [passwordResetAllowed, setPasswordResetAllowed] = useState(false);

  async function refreshSession() {
    const result = await getAuthSession();
    if (result.authenticated) {
      setUser({ email: result.principal.subject });
      setPasswordConfigured(Boolean(result.password_configured));
      setPasswordResetAllowed(Boolean(result.password_reset_allowed));
    }
    return result;
  }

  useEffect(() => {
    let active = true;
    getAuthSession()
      .then((result) => {
        if (active && result.authenticated) {
          setUser({ email: result.principal.subject });
          setPasswordConfigured(Boolean(result.password_configured));
          setPasswordResetAllowed(Boolean(result.password_reset_allowed));
        }
      })
      .catch(() => {})
      .finally(() => {
        if (active) setAuthReady(true);
      });
    return () => {
      active = false;
    };
  }, []);

  const value = useMemo(() => ({
    user,
    authReady,
    pendingEmail,
    challengeId,
    emailVerified,
    twoFactorEnabled,
    rememberDevice,
    passwordConfigured,
    passwordResetAllowed,
    refreshSession,
    isAuthenticated: Boolean(user),
    async beginSignIn(email, options = {}) {
      const normalizedEmail = email.trim();
      setPendingEmail(normalizedEmail);
      setRememberDevice(Boolean(options.remember));
      const result = await requestEmailChallenge(normalizedEmail);
      setChallengeId(result.challenge_id);
      return { requiresTwoFactor: true };
    },
    async completeTwoFactor(code) {
      const result = await verifyEmailChallenge({ challengeId, code });
      const email = result.email || pendingEmail;
      setUser({ email });
      setPendingEmail('');
      setChallengeId('');
      await refreshSession();
    },
    async signInWithPassword(email, password) {
      await passwordSignInRequest({ email: email.trim(), password });
      await refreshSession();
    },
    register({ fullName, email }) {
      setPendingEmail(email.trim());
      setEmailVerified(false);
      setTwoFactorEnabled(false);
      setRememberDevice(false);
      setPasswordResetAllowed(false);
      return { fullName: fullName.trim(), email: email.trim() };
    },
    verifyEmail() {
      setEmailVerified(true);
    },
    setTwoFactorEnabled,
    signOut() {
      setUser(null);
      setPendingEmail('');
      setChallengeId('');
      setRememberDevice(false);
      void destroyAuthSession().catch(() => {});
    },
  }), [authReady, challengeId, emailVerified, passwordConfigured, passwordResetAllowed, pendingEmail, rememberDevice, twoFactorEnabled, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }

  return context;
}
