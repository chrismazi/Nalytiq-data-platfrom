/**
 * Enhanced API hooks with error handling and loading states
 */

import { useState, useCallback } from 'react';
import { apiClient, api, APIError, NetworkError, ValidationError } from '@/lib/api-client';
import { toast } from '@/lib/toast';

interface UseApiOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
  showSuccessToast?: boolean;
  showErrorToast?: boolean;
  successMessage?: string;
}

interface ApiState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
}

export function useApi<T = any>(options: UseApiOptions = {}) {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    error: null,
    loading: false,
  });

  const execute = useCallback(
    async (apiCall: () => Promise<T>): Promise<T | null> => {
      setState({ data: null, error: null, loading: true });

      try {
        const data = await apiCall();
        
        setState({ data, error: null, loading: false });
        
        if (options.onSuccess) {
          options.onSuccess(data);
        }
        
        if (options.showSuccessToast && options.successMessage) {
          toast.success(options.successMessage);
        }
        
        return data;
      } catch (error) {
        const err = error as Error;
        setState({ data: null, error: err, loading: false });
        
        if (options.onError) {
          options.onError(err);
        }
        
        if (options.showErrorToast !== false) {
          handleApiError(err);
        }
        
        return null;
      }
    },
    [options]
  );

  const reset = useCallback(() => {
    setState({ data: null, error: null, loading: false });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

export function useFileUpload() {
  const { execute, ...state } = useApi({
    showErrorToast: true,
  });

  const upload = useCallback(
    async (endpoint: string, file: File, additionalData?: Record<string, string>) => {
      const loadingToast = toast.loading(`Uploading ${file.name}...`);
      
      try {
        const result = await execute(() =>
          apiClient.uploadFile(endpoint, file, additionalData)
        );
        
        toast.dismiss(loadingToast);
        
        if (result) {
          toast.uploadSuccess(file.name);
        }
        
        return result;
      } catch (error) {
        toast.dismiss(loadingToast);
        throw error;
      }
    },
    [execute]
  );

  return {
    upload,
    ...state,
  };
}

export function useAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true);
    setError(null);

    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await apiClient.post<{ access_token: string; token_type: string }>(
        '/auth/login', 
        formData.toString(), 
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          } as any,
        }
      );

      if (typeof window !== 'undefined') {
        localStorage.setItem('token', response.access_token);
      }

      toast.success('Login successful');
      return response;
    } catch (err) {
      const errorMessage = api.handleError(err);
      setError(errorMessage);
      toast.error(errorMessage, { title: 'Login Failed' });
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (email: string, password: string, role: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post('/auth/register', {
        email,
        password,
        role,
      });

      toast.success('Registration successful. Please log in.');
      return response;
    } catch (err) {
      const errorMessage = api.handleError(err);
      setError(errorMessage);
      toast.error(errorMessage, { title: 'Registration Failed' });
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    toast.info('Logged out successfully');
  }, []);

  return {
    login,
    register,
    logout,
    loading,
    error,
  };
}

// Helper function to handle API errors
function handleApiError(error: Error) {
  if (error instanceof ValidationError) {
    toast.validationError(Object.values(error.errors).flat());
  } else if (error instanceof APIError) {
    if (error.statusCode === 401) {
      toast.sessionExpired();
    } else {
      toast.error(error.message);
    }
  } else if (error instanceof NetworkError) {
    toast.networkError();
  } else {
    toast.error(error.message || 'An unexpected error occurred');
  }
}

// Specific hooks for common operations
export function useDataAnalysis() {
  return useApi({
    showSuccessToast: true,
    successMessage: 'Analysis completed successfully',
  });
}

export function useDataExport() {
  return useApi({
    showSuccessToast: true,
    successMessage: 'Data exported successfully',
  });
}
