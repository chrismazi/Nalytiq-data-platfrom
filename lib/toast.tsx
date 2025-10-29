/**
 * Enhanced toast notification system
 * Built on top of sonner for better UX
 */

import { toast as sonnerToast } from 'sonner';
import { CheckCircle2, XCircle, AlertCircle, Info, Loader2 } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info' | 'loading';

interface ToastOptions {
  title?: string;
  description?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

class ToastManager {
  success(message: string, options?: ToastOptions) {
    return sonnerToast.success(options?.title || 'Success', {
      description: message,
      duration: options?.duration || 4000,
      icon: <CheckCircle2 className="h-5 w-5" />,
      action: options?.action,
    });
  }

  error(message: string, options?: ToastOptions) {
    return sonnerToast.error(options?.title || 'Error', {
      description: message,
      duration: options?.duration || 6000,
      icon: <XCircle className="h-5 w-5" />,
      action: options?.action,
    });
  }

  warning(message: string, options?: ToastOptions) {
    return sonnerToast.warning(options?.title || 'Warning', {
      description: message,
      duration: options?.duration || 5000,
      icon: <AlertCircle className="h-5 w-5" />,
      action: options?.action,
    });
  }

  info(message: string, options?: ToastOptions) {
    return sonnerToast.info(options?.title || 'Info', {
      description: message,
      duration: options?.duration || 4000,
      icon: <Info className="h-5 w-5" />,
      action: options?.action,
    });
  }

  loading(message: string, options?: Omit<ToastOptions, 'duration'>) {
    return sonnerToast.loading(options?.title || 'Loading', {
      description: message,
      icon: <Loader2 className="h-5 w-5 animate-spin" />,
    });
  }

  promise<T>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: any) => string);
    }
  ) {
    return sonnerToast.promise(promise, {
      loading: messages.loading,
      success: messages.success,
      error: messages.error,
    });
  }

  dismiss(toastId?: string | number) {
    if (toastId) {
      sonnerToast.dismiss(toastId);
    } else {
      sonnerToast.dismiss();
    }
  }

  // Custom toasts for specific scenarios
  uploadSuccess(filename: string) {
    return this.success(`${filename} uploaded successfully`, {
      title: 'Upload Complete',
    });
  }

  uploadError(filename: string, error: string) {
    return this.error(`Failed to upload ${filename}: ${error}`, {
      title: 'Upload Failed',
      duration: 8000,
    });
  }

  analysisComplete(recordCount: number) {
    return this.success(
      `Analysis complete for ${recordCount.toLocaleString()} records`,
      {
        title: 'Analysis Complete',
      }
    );
  }

  networkError() {
    return this.error(
      'Unable to connect to the server. Please check your internet connection.',
      {
        title: 'Connection Error',
        duration: 8000,
      }
    );
  }

  validationError(errors: string[]) {
    return this.error(
      errors.join(', '),
      {
        title: 'Validation Failed',
        duration: 6000,
      }
    );
  }

  sessionExpired() {
    return this.warning(
      'Your session has expired. Please log in again.',
      {
        title: 'Session Expired',
        duration: 6000,
        action: {
          label: 'Login',
          onClick: () => {
            window.location.href = '/login';
          },
        },
      }
    );
  }
}

export const toast = new ToastManager();
