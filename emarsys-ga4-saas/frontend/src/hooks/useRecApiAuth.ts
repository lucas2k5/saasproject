import { useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import recApi, { setRecApiToken } from '../api/recommendations/axios';

/**
 * Bridges Supabase auth → recommendation-service auth.
 * Auto-registers / logs in using the Supabase user's email
 * so the rec API gets its own valid JWT.
 */
export function useRecApiAuth() {
  const { session } = useAuth();
  const authenticating = useRef(false);

  useEffect(() => {
    const email = session?.user?.email;
    if (!email || authenticating.current) return;

    authenticating.current = true;

    // Derive a stable password from the Supabase user id
    const derivedPass = `RecSvc_${session.user.id}`;

    (async () => {
      try {
        // Try login first
        const form = new URLSearchParams();
        form.append('username', email);
        form.append('password', derivedPass);

        let res = await recApi.post('/auth/login', form, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });

        setRecApiToken(res.data.access_token);
      } catch (loginErr: any) {
        // If login failed (401/404), register then retry
        if (loginErr?.response?.status === 401 || loginErr?.response?.status === 404) {
          try {
            const regRes = await recApi.post('/auth/register', {
              email,
              password: derivedPass,
              full_name: session.user.user_metadata?.full_name || email.split('@')[0],
              company_name: 'KeepAIS',
            });
            setRecApiToken(regRes.data.access_token);
          } catch (regErr: any) {
            // Maybe another tab already registered — try login once more
            try {
              const form = new URLSearchParams();
              form.append('username', email);
              form.append('password', derivedPass);
              const res = await recApi.post('/auth/login', form, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
              });
              setRecApiToken(res.data.access_token);
            } catch {
              console.error('[useRecApiAuth] Failed to authenticate with recommendation service');
            }
          }
        } else {
          console.error('[useRecApiAuth] Unexpected login error', loginErr);
        }
      } finally {
        authenticating.current = false;
      }
    })();
  }, [session?.user?.email, session?.user?.id]);
}
