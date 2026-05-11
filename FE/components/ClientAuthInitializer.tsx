'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';

const ClientAuthInitializer = () => {
  const initializeAuth = useAuthStore((state) => state.initializeAuth);

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return null; // no UI, just initializes auth
};

export default ClientAuthInitializer;
