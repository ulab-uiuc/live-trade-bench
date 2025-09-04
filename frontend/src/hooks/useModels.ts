import { useCallback, useEffect, useMemo, useState } from 'react';
import type { Model } from '../types';

export function useModelsByCategory(category: 'stock' | 'polymarket') {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date(0));

  const fetchModels = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/models/');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const allModels = await response.json();
      const filtered = (allModels as Model[]).filter(m => m.category === category);
      setModels(filtered);
      setLastRefresh(new Date());
    } catch (e: any) {
      console.error('useModelsByCategory:', e);
      setError('Failed to load models');
    } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => {
    // initial fetch and refresh every 60s
    fetchModels();
    const id = setInterval(fetchModels, 60000);
    return () => clearInterval(id);
  }, [fetchModels]);

  const stats = useMemo(() => {
    const totalProfit = models.reduce((sum, m) => sum + (m.profit || 0), 0);
    const activeModels = models.filter(m => m.status === 'active').length;
    return { totalProfit, activeModels, totalModels: models.length };
  }, [models]);

  return { models, loading, error, refresh: fetchModels, lastRefresh, stats };
}
