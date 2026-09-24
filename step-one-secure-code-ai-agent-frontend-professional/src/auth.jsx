import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import {
  destroyAuthSession,
  getAuthSession,
  requestEmailChallenge,
  verifyEmailChallenge,
} from './api/endpoints';

const AuthContext = createContext(null);

const DEFAULT_USER = {
  id: 'verified-local-user',
  name: 'Security Engineer',
  email: '',
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [pendingEmail, setPendingEmail] = useState('');
  const [challengeId, setChallengeId] = useState('');
  const [emailVerified, setEmailVerified] = useState(true);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(true);
  const [rememberDevice, setRememberDevice] = useState(false);

  useEffect(() => {
    let active = true;
    getAuthSession()
      .then((result) => {
        if (active && result.authenticated) {
          setUser({
            ...DEFAULT_USER,
            email: result.principal.subject,
          });
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
      const email = result.email || pendingEmail || DEFAULT_USER.email;
      setUser({ ...DEFAULT_USER, email });
      setPendingEmail('');
      setChallengeId('');
    },
    register({ fullName, email }) {
      setPendingEmail(email.trim());
      setEmailVerified(false);
      setTwoFactorEnabled(false);
      setRememberDevice(false);
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
  }), [authReady, challengeId, emailVerified, pendingEmail, rememberDevice, twoFactorEnabled, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }

  return context;
}
