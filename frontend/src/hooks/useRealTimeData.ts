import { useState, useEffect, useCallback, useRef } from 'react';

interface UseRealTimeDataOptions {
  url: string;
  refreshInterval?: number; // in milliseconds
  enabled?: boolean;
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
  immediate?: boolean; // fetch immediately on mount
}

export const useRealTimeData = <T>({
  url,
  refreshInterval = 30000, // 30 seconds default
  enabled = true,
  onSuccess,
  onError,
  immediate = true
}: UseRealTimeDataOptions) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchData = useCallback(async () => {
    if (!enabled || !url) return;

    setLoading(true);
    setError(null);

    // Cancel previous request if still pending
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(url, {
        signal: abortControllerRef.current.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
      setLastUpdated(new Date());
      onSuccess?.(result);
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        setError(err);
        onError?.(err);
      }
    } finally {
      setLoading(false);
    }
  }, [url, enabled, onSuccess, onError]);

  const startPolling = useCallback(() => {
    if (!enabled || intervalRef.current) return;

    intervalRef.current = setInterval(fetchData, refreshInterval);
  }, [fetchData, refreshInterval, enabled]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const refetch = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (immediate) {
      fetchData();
    }

    if (enabled) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => {
      stopPolling();
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchData, startPolling, stopPolling, enabled, immediate]);

  useEffect(() => {
    return () => {
      stopPolling();
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [stopPolling]);

  return {
    data,
    loading,
    error,
    lastUpdated,
    refetch,
    startPolling,
    stopPolling
  };
};

export default useRealTimeData;
