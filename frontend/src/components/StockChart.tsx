import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    ChartOptions,
    ChartData,
    Plugin
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { Model } from '../types';
import './StockChart.css';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

interface StockChartProps {
    modelsData: any[];
    historyData: any[];
    timeRange: '1M' | 'ALL';
    category: 'stock' | 'polymarket' | 'bitmex';
    onModelClick?: (model: any) => void;
}

interface ChartPoint {
    x: number; // Timestamp
    y: number; // Value
    date: string;
}

interface ModelHistory {
    id: string;
    name: string;
    data: ChartPoint[];
    color: string;
    icon?: string;
}

const StockChart: React.FC<StockChartProps> = ({
    modelsData,
    historyData,
    timeRange,
    category,
    onModelClick
}) => {
    const [hoveredModelId, setHoveredModelId] = useState<string | null>(null);
    const [verticalLineX, setVerticalLineX] = useState<number | null>(null);
    const [tooltipData, setTooltipData] = useState<any | null>(null);
    const [imagesLoaded, setImagesLoaded] = useState<boolean>(false);
    const [showLabels, setShowLabels] = useState(true);

    const chartRef = useRef<any>(null);
    const imagesRef = useRef<{ [key: string]: HTMLImageElement }>({});
    const filteredDataRef = useRef<any[]>([]);
    const mouseXRef = useRef<number | null>(null);
    const isHoveringIconRef = useRef(false);
    const [resizeCount, setResizeCount] = useState(0);

    // ...




    // Preload images
    useEffect(() => {
        const providers = ['OpenAI', 'Anthropic', 'Google', 'Meta', 'Benchmark', 'Moonshot', 'Qwen', 'DeepSeek', 'xAI'];
        const loadImages = async () => {
            const promises = providers.map(p => {
                return new Promise<void>((resolve) => {
                    const img = new Image();
                    let src = '/benchmark.png';
                    if (p === 'OpenAI') src = '/openai.png';
                    else if (p === 'Anthropic') src = '/claude.png';
                    else if (p === 'Google') src = '/google.png';
                    else if (p === 'Meta') src = '/meta.png';
                    else if (p === 'Moonshot') src = '/kimi.png';
                    else if (p === 'Qwen') src = '/qwen.png';
                    else if (p === 'DeepSeek') src = '/deepseek.png';
                    else if (p === 'xAI') src = '/xai.png';

                    img.src = src;
                    img.onload = () => {
                        imagesRef.current[p] = img;
                        resolve();
                    };
                    img.onerror = () => {
                        // Fallback or just resolve
                        resolve();
                    };
                });
            });
            await Promise.all(promises);
            setImagesLoaded(true);
        };
        loadImages();
    }, []);

    // Data is now provided via props from App.tsx - no need to fetch

    // Process data for chart
    const processedData = useMemo(() => {
        const sourceData = timeRange === '1M' ? modelsData : historyData;

        if (!sourceData || sourceData.length === 0) {
            return [];
        }

        // Filter by category
        const categoryFiltered = sourceData.filter((m: any) => {
            const cat = (m.category || "").toString().toLowerCase();
            const name = (m.name || "").toString().toUpperCase();

            // Exclude QQQ and VOO from stock chart
            if (category === 'stock' && (name.includes('QQQ') || name.includes('VOO'))) {
                return false;
            }

            if (category === 'stock') {
                return cat === 'stock' || cat === 'benchmark';
            }
            if (category === 'polymarket') {
                return cat.includes('poly');
            }
            if (category === 'bitmex') {
                return cat === 'bitmex' || cat === 'bitmex-benchmark';
            }
            return false;
        });

        // Helper to parse history
        const parseHistory = (model: any) => {
            const history = model.profitHistory || [];
            return history.map((h: any) => {
                const rawTs: string = h.timestamp;
                if (!rawTs) return null;

                // Normalize timestamp: treat naive strings as UTC, then remap date-only points to EST close time (15:30) to keep calendar days aligned.
                let timestampStr = rawTs;
                const hasExplicitTime = /T\d{2}:\d{2}/.test(rawTs);
                if (timestampStr && !timestampStr.endsWith('Z') && !timestampStr.includes('+') && !timestampStr.includes('-', 10)) {
                    timestampStr = timestampStr + 'Z';
                }

                const parsedDate = new Date(timestampStr);
                if (isNaN(parsedDate.getTime())) return null;

                const estOffsetMinutes = getTimeZoneOffset(parsedDate, 'America/New_York');
                let effectiveMs = parsedDate.getTime();

                // If no explicit time (daily data), anchor to 15:30 EST so the day doesn't shift backward when displayed in EST.
                if (!hasExplicitTime || (parsedDate.getUTCHours() === 0 && parsedDate.getUTCMinutes() === 0 && parsedDate.getUTCSeconds() === 0)) {
                    const year = parsedDate.getUTCFullYear();
                    const month = parsedDate.getUTCMonth();
                    const day = parsedDate.getUTCDate();
                    const closeUtc = Date.UTC(year, month, day, 15, 30, 0, 0) - (estOffsetMinutes * 60 * 1000);
                    effectiveMs = closeUtc;
                }

                const effectiveDate = new Date(effectiveMs);

                return {
                    x: effectiveMs,
                    y: h.totalValue || h.profit || 0,  // Use totalValue if available, fallback to profit
                    date: effectiveDate.toISOString(),  // Store display time aligned to EST
                    originalX: effectiveMs
                };
            })
                .filter((p: any) => p !== null)
                .sort((a: any, b: any) => a.x - b.x);
        };

        const parsedModels = categoryFiltered.map((model: any) => {
            const parsedData = parseHistory(model);
            return {
                id: model.id,
                name: model.name,
                category: model.category,
                provider: extractProvider(model.name),
                data: parsedData,
                color: getModelColor(model.name),
                rawData: parsedData // Keep original data
            };
        });

        // Find the minimum timestamp across all models to normalize X-axis
        let minTimestamp = Infinity;
        parsedModels.forEach(model => {
            if (model.data.length > 0) {
                const firstTimestamp = model.data[0].x;
                if (firstTimestamp < minTimestamp) {
                    minTimestamp = firstTimestamp;
                }
            }
        });

        // Normalize all timestamps to start from 0
        return parsedModels.map(model => ({
            ...model,
            data: model.data.map((p: ChartPoint) => ({
                ...p,
                x: p.x - minTimestamp, // Normalize to 0-based
                originalX: p.x // Keep original for date display
            }))
        }));
    }, [modelsData, historyData, timeRange, category]);

    // Filter data based on time range
    const filteredData = useMemo(() => {
        if (timeRange === 'ALL') return processedData;

        const oneMonthAgo = new Date();
        oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
        const cutoff = oneMonthAgo.getTime();

        const filtered = processedData.map((model: any) => ({
            ...model,
            data: model.data.filter((p: any) => p.originalX >= cutoff) // Use originalX for time comparison
        }));

        // Re-normalize the filtered data so x=0 is the earliest visible date
        let minFilteredTimestamp = Infinity;
        filtered.forEach(model => {
            if (model.data.length > 0) {
                const firstOriginal = (model.data[0] as any).originalX;
                if (firstOriginal < minFilteredTimestamp) {
                    minFilteredTimestamp = firstOriginal;
                }
            }
        });

        // Re-normalize to start from 0
        return filtered.map(model => ({
            ...model,
            data: model.data.map((p: any) => ({
                ...p,
                x: p.originalX - minFilteredTimestamp // Re-normalize based on filtered data
            }))
        }));
    }, [processedData, timeRange]);

    // Keep ref updated with latest filteredData
    useEffect(() => {
        filteredDataRef.current = filteredData;
    }, [filteredData]);

    // Hide labels during tab switch to prevent position flicker
    useEffect(() => {
        setShowLabels(false);
        // Wait for chart to re-render (2 animation frames)
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                setShowLabels(true);
            });
        });
    }, [category, timeRange]);

    // Chart Data Construction
    const chartData: ChartData<'line'> = useMemo(() => {
        const datasets = filteredData.map(model => {
            const isHovered = hoveredModelId === model.id;
            const isAnyHovered = hoveredModelId !== null;

            // Color logic: if something is hovered and it's not this one, grey it out
            const borderColor = isAnyHovered && !isHovered ? '#374151' : model.color; // Dark grey for dimmed
            const borderWidth = isHovered ? 3 : 2;
            const zIndex = isHovered ? 10 : 1;

            return {
                label: model.name,
                data: model.data.map((p: ChartPoint) => ({ x: p.x, y: p.y })),
                borderColor,
                backgroundColor: 'transparent',
                borderWidth,
                pointRadius: 0, // Hide points by default
                pointHoverRadius: 0,
                tension: 0, // Straight lines between nodes
                order: isHovered ? -1 : 1, // Bring hovered to front
            };
        });

        return { datasets };
    }, [filteredData, hoveredModelId]);

    // Build x-axis ticks from actual data points but subsampled to keep the axis uncluttered.
    const tickValues = useMemo(() => {
        const allX: number[] = [];
        filteredData.forEach(model => {
            model.data.forEach((p: any) => {
                if (typeof p.x === 'number') {
                    allX.push(p.x);
                }
            });
        });
        if (!allX.length) return [];
        const uniqueSorted = Array.from(new Set(allX)).sort((a, b) => a - b);
        const maxTicks = 8;
        if (uniqueSorted.length <= maxTicks) return uniqueSorted;

        const minX = uniqueSorted[0];
        const maxX = uniqueSorted[uniqueSorted.length - 1];
        const targetStep = (maxX - minX) / (maxTicks - 1);
        const ticks: number[] = [];

        // Walk through uniqueSorted once to pick nearest points to evenly spaced targets
        let cursor = 0;
        for (let i = 0; i < maxTicks; i++) {
            const target = minX + i * targetStep;
            while (cursor + 1 < uniqueSorted.length &&
                Math.abs(uniqueSorted[cursor + 1] - target) < Math.abs(uniqueSorted[cursor] - target)) {
                cursor += 1;
            }
            ticks.push(uniqueSorted[cursor]);
        }

        return Array.from(new Set(ticks));
    }, [filteredData]);

    // Custom Plugin for Vertical Line and Tooltip
    const verticalLinePlugin: Plugin = useMemo(() => ({
        id: 'verticalLine',
        afterDraw: (chart) => {
            // Calculate max data X pixel to restrict tooltip area
            let maxDataX = 0;
            const currentFilteredData = filteredDataRef.current;
            currentFilteredData.forEach(model => {
                if (model.data.length > 0) {
                    const lastX = model.data[model.data.length - 1].x;
                    if (lastX > maxDataX) maxDataX = lastX;
                }
            });
            const maxDataPixel = chart.scales.x.getPixelForValue(maxDataX);

            // Check if mouse is to the right of the data (with a small buffer)
            if (mouseXRef.current !== null && mouseXRef.current > maxDataPixel + 5) {
                setVerticalLineX(null);
                setTooltipData(null);
                return;
            }

            const activeElements = chart.tooltip?.getActiveElements?.() || chart.tooltip?.dataPoints;
            if (!activeElements || activeElements.length === 0) {
                setVerticalLineX(null);
                setTooltipData(null);
                return;
            }

            if (activeElements && activeElements.length > 0) {
                const ctx = chart.ctx;
                const x = activeElements[0].element.x;
                const topY = chart.scales.y.top;
                const bottomY = chart.scales.y.bottom;

                // Draw vertical line
                ctx.save();
                ctx.beginPath();
                ctx.moveTo(x, topY);
                ctx.lineTo(x, bottomY);
                ctx.lineWidth = 1;
                ctx.strokeStyle = '#4b5563'; // Darker grey
                ctx.setLineDash([5, 5]);
                ctx.stroke();
                ctx.restore();

                // Update state for custom tooltip rendering outside canvas
                // We only do this if the X has changed significantly to avoid re-renders
                if (verticalLineX !== x) {
                    setVerticalLineX(x);
                    // Extract data for all models at this X index
                    const dataIndex = (activeElements[0] as any).index ?? (activeElements[0] as any).dataIndex ?? 0;
                    const currentFilteredData = filteredDataRef.current;

                    const currentData = currentFilteredData.map(m => ({
                        ...m,
                        currentValue: m.data[dataIndex]?.y,
                        currentDate: m.data[dataIndex]?.date
                    })).sort((a, b) => (b.currentValue || 0) - (a.currentValue || 0));

                    setTooltipData({
                        x,
                        data: currentData,
                        date: currentData[0]?.currentDate,
                        dataIndex,
                        totalDataPoints: currentFilteredData[0]?.data.length || 0
                    });
                }
            }
        }
    }), [filteredData, verticalLineX]);

    // Calculate max X for chart with padding
    const maxX = useMemo(() => {
        let max = 0;
        filteredData.forEach(model => {
            if (model.data.length > 0) {
                const lastX = model.data[model.data.length - 1].x;
                if (lastX > max) max = lastX;
            }
        });
        return max * 1.15; // Add 25% padding for labels
    }, [filteredData]);

    const options: ChartOptions<'line'> = {
        responsive: true,
        maintainAspectRatio: false,
        onResize: () => {
            // Force re-render of labels when chart resizes
            setResizeCount(c => c + 1);
        },
        animation: {
            duration: 0 // Disable animation for instant rendering
        },
        interaction: {
            mode: 'index', // prioritize same X index
            intersect: false,
            axis: 'x'
        },
        layout: {
            padding: {
                right: 100 // Space for labels
            }
        },
        plugins: {
            legend: {
                display: false // Custom legend/labels
            },
            tooltip: {
                enabled: false, // Disable default tooltip
                external: () => { } // We handle it with the plugin/state
            }
        },
        scales: {
            x: {
                type: 'linear',
                display: true,
                min: 0,
                max: maxX,
                grid: {
                    display: true,
                    color: '#374151' // Dark grid
                },
                ticks: {
                    callback: (value, index, ticks) => {
                        // We need to reconstruct the actual date from the normalized value
                        // Get the first data point to find minTimestamp
                        if (filteredData.length > 0 && filteredData[0].data.length > 0) {
                            const firstPoint = filteredData[0].data[0];
                            const minTimestamp = (firstPoint as any).originalX - firstPoint.x;
                            const actualTimestamp = (value as number) + minTimestamp;
                            const date = new Date(actualTimestamp);

                            if (!isNaN(date.getTime())) {
                                try {
                                    const isLastTick = index === ticks.length - 1;
                                    const monthDay = date.toLocaleDateString('en-US', {
                                        month: 'short',
                                        day: 'numeric',
                                        timeZone: 'America/New_York'
                                    });

                                    // Show real time (EST) for the last tick or when data carries a time component
                                    const hasTimeComponent = date.getUTCHours() !== 0 || date.getUTCMinutes() !== 0;
                                    if (isLastTick || hasTimeComponent) {
                                        const time = date.toLocaleTimeString('en-US', {
                                            hour: '2-digit',
                                            minute: '2-digit',
                                            hour12: false,
                                            timeZone: 'America/New_York'
                                        });
                                        return `${monthDay} ${time} EST`;
                                    }

                                    return `${monthDay} EST`;
                                } catch (e) {
                                    return `${index + 1}`;
                                }
                            }
                        }
                        return `Day ${index + 1}`;
                    },
                    maxTicksLimit: tickValues.length || 8,
                    color: '#9ca3af',
                    font: {
                        size: 10,
                        family: 'Inter, sans-serif'
                    }
                },
                afterBuildTicks: (scale) => {
                    if (!tickValues.length) return;
                    (scale as any).ticks = tickValues.map(v => ({ value: v }));
                }
            },
            y: {
                display: true,
                position: 'left',
                title: {
                    display: true,
                    text: 'Total Value',
                    color: '#9ca3af',
                    font: {
                        size: 12,
                        weight: 'bold',
                        family: 'Inter, sans-serif'
                    }
                },
                grid: {
                    color: '#374151' // Dark grid
                },
                ticks: {
                    callback: (value) => `$${value.toLocaleString()}`,
                    color: '#9ca3af',
                    font: {
                        size: 10,
                        family: 'Inter, sans-serif'
                    }
                }
            }
        },
        onHover: (event, elements) => {
            // Track mouse X position
            if (event.x !== null && event.x !== undefined) {
                mouseXRef.current = event.x;
            }

            const chart = chartRef.current;
            if (!chart) return;

            const currentFiltered = filteredDataRef.current;
            if (!currentFiltered?.length) return;

            const xScale: any = chart.scales?.x;
            if (!xScale || typeof xScale.getValueForPixel !== 'function') return;

            const hoveredX = xScale.getValueForPixel(event.x);
            if (hoveredX === null || hoveredX === undefined || Number.isNaN(hoveredX)) return;

            // Prefer Chart.js computed elements (mouse truly on/near a line)
            if (elements && elements.length > 0) {
                // Pick the closest element to the pointer (by Euclidean distance)
                let nearest = elements[0] as any;
                let bestD = Infinity;
                elements.forEach((el: any) => {
                    const dx = (el.element?.x ?? 0) - (event.x ?? 0);
                    const dy = (el.element?.y ?? 0) - (event.y ?? 0);
                    const d = dx * dx + dy * dy;
                    if (d < bestD) {
                        bestD = d;
                        nearest = el;
                    }
                });

                const bestDistance = Math.sqrt(bestD);
                const SNAP_THRESHOLD = 24; // px
                if (bestDistance <= SNAP_THRESHOLD) {
                    const activeElements = [{
                        datasetIndex: nearest.datasetIndex,
                        index: nearest.index
                    }];

                    const datasetIndex = nearest.datasetIndex;
                    const modelId = filteredData[datasetIndex]?.id;
                    if (modelId && hoveredModelId !== modelId) {
                        setHoveredModelId(modelId);
                    }

                    chart.setActiveElements(activeElements);
                    chart.tooltip?.setActiveElements(activeElements, { x: event.x, y: event.y });
                    chart.update();
                    return;
                }
            }

            // Otherwise, synthesize active elements based purely on X (mouse can be off the line)
            // Use the longest series as baseline for nearest-index mapping to avoid gaps
            let baselineIdx = 0;
            let baseline = currentFiltered[0];
            currentFiltered.forEach((m: any, idx: number) => {
                const len = m.data?.length || 0;
                const baselineLen = baseline?.data?.length || 0;
                if (len > baselineLen) {
                    baseline = m;
                    baselineIdx = idx;
                }
            });
            if (!baseline?.data?.length) return;

            // Find nearest index on baseline
            let nearestIdx = 0;
            let bestDiff = Infinity;
            baseline.data.forEach((p: any, idx: number) => {
                if (typeof p.x !== 'number') return;
                const diff = Math.abs(p.x - hoveredX);
                if (diff < bestDiff) {
                    bestDiff = diff;
                    nearestIdx = idx;
                }
            });

            const activeElements: { datasetIndex: number; index: number }[] = [];

            // Baseline first to drive vertical line x position
            const baseLast = (baseline.data?.length || 0) - 1;
            const baseIdx = Math.min(nearestIdx, baseLast);
            if (baseline.data?.[baseIdx] && chart.getDatasetMeta(baselineIdx)?.data?.[baseIdx]) {
                activeElements.push({ datasetIndex: baselineIdx, index: baseIdx });
            }

            // Other datasets aligned to same nearest index (clamped to their length)
            currentFiltered.forEach((m: any, datasetIndex: number) => {
                if (datasetIndex === baselineIdx) return;
                const lastIdx = (m.data?.length || 0) - 1;
                if (lastIdx < 0) return;
                const idx = Math.min(nearestIdx, lastIdx);
                if (!m.data[idx]) return;
                const meta = chart.getDatasetMeta(datasetIndex);
                if (!(meta?.data && meta.data[idx])) return;
                activeElements.push({ datasetIndex, index: idx });
            });

            if (!activeElements.length) {
                if (!isHoveringIconRef.current) setHoveredModelId(null);
                return;
            }

            // Off-line hover: don't force-highlight a specific model; clear unless over icons
            if (!isHoveringIconRef.current && hoveredModelId !== null) {
                setHoveredModelId(null);
            }

            chart.setActiveElements(activeElements);
            chart.tooltip?.setActiveElements(activeElements, { x: event.x, y: event.y });
            chart.update();
        }
    };

    return (
        <div className="stock-chart-container">
            <div
                className="chart-wrapper"
                onMouseLeave={() => {
                    setHoveredModelId(null);
                    setVerticalLineX(null);
                    setTooltipData(null);
                    const chart = chartRef.current;
                    chart?.setActiveElements([]);
                    chart?.tooltip?.setActiveElements([], { x: 0, y: 0 });
                    chart?.update();
                }}
            >
                <Line
                    ref={chartRef}
                    data={chartData}
                    options={options}
                    plugins={[verticalLinePlugin]}
                />

                {/* Custom Labels on the right side */}
                {showLabels && filteredData.length > 0 && chartRef.current && (
                    <div key={resizeCount} style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none' }}>
                        {filteredData.map((model, index) => {
                            const chart = chartRef.current;
                            if (!chart) return null;

                            const meta = chart.getDatasetMeta(index);
                            if (!meta || meta.hidden) return null;

                            const lastIndex = meta.data?.length - 1;
                            if (lastIndex < 0) return null;

                            const lastPoint = meta.data[lastIndex];
                            if (!lastPoint) return null;

                            const isHovered = hoveredModelId === model.id;
                            const isAnyHovered = hoveredModelId !== null;
                            const opacity = isAnyHovered && !isHovered ? 0.3 : 1;

                            // Use same icon logic as Dashboard ProviderIcon
                            const getProviderIcon = (provider?: string, name?: string) => {
                                const p = provider?.toLowerCase() || "";
                                const n = name?.toLowerCase() || "";

                                if (p.includes("openai") || p.includes("gpt") || n.includes("gpt")) {
                                    return "./openai.png";
                                }
                                if (p.includes("anthropic") || p.includes("claude") || n.includes("claude")) {
                                    return `${process.env.PUBLIC_URL}/claude.png`;
                                }
                                if (p.includes("google") || p.includes("gemini") || n.includes("gemini")) {
                                    return "./google.png";
                                }
                                if (p.includes("meta") || p.includes("llama") || n.includes("llama")) {
                                    return "./meta.png";
                                }
                                if (p.includes("kimi") || n.includes("kimi")) {
                                    return "./kimi.png";
                                }
                                if (p.includes("qwen") || n.includes("qwen")) {
                                    return "./qwen.png";
                                }
                                if (p.includes("deepseek") || n.includes("deepseek")) {
                                    return "./deepseek.png";
                                }
                                if (p.includes("xai") || p.includes("grok") || n.includes("grok")) {
                                    return "./xai.png";
                                }
                                return "./benchmark.png";
                            };

                            const getProviderClass = (provider?: string, name?: string) => {
                                const p = provider?.toLowerCase() || "";
                                const n = name?.toLowerCase() || "";
                                if (p.includes("openai") || p.includes("gpt") || n.includes("gpt")) return "openai";
                                if (p.includes("anthropic") || p.includes("claude") || n.includes("claude")) return "anthropic";
                                if (p.includes("google") || p.includes("gemini") || n.includes("gemini")) return "google";
                                if (p.includes("meta") || p.includes("llama") || n.includes("llama")) return "meta";
                                if (p.includes("qwen") || n.includes("qwen") || p.includes("kimi") || n.includes("kimi")) return "kimi";
                                if (p.includes("deepseek") || n.includes("deepseek")) return "deepseek";
                                if (p.includes("xai") || p.includes("grok") || n.includes("grok")) return "xai";
                                return "other";
                            };

                            const iconSrc = getProviderIcon(model.provider, model.name);
                            const isBenchmarkIcon = iconSrc.includes('benchmark');
                            const cls = isBenchmarkIcon ? 'benchmark' : getProviderClass(model.provider, model.name);

                            return (
                                <div
                                    key={model.id}
                                    style={{
                                        position: 'absolute',
                                        left: lastPoint.x + 8,
                                        top: lastPoint.y - 12,
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        pointerEvents: 'auto',
                                        cursor: onModelClick ? 'pointer' : 'default',
                                        opacity,
                                        transition: 'opacity 0.2s',
                                        whiteSpace: 'nowrap'
                                    }}
                                    onClick={() => onModelClick?.(model)}
                                    onMouseEnter={() => {
                                        isHoveringIconRef.current = true;
                                        setHoveredModelId(model.id);
                                    }}
                                    onMouseLeave={() => {
                                        isHoveringIconRef.current = false;
                                        setHoveredModelId(null);
                                    }}
                                >
                                    <div className={`model-avatar ${cls}`} title={model.provider || model.name}>
                                        <img
                                            src={iconSrc}
                                            alt={model.name}
                                            style={{ width: '18px', height: '18px', objectFit: 'contain' }}
                                            onError={(e) => {
                                                // Fallback to emoji if image fails to load
                                                e.currentTarget.style.display = 'none';
                                                e.currentTarget.parentElement!.innerHTML = '<span style="line-height: 1; display: block;">⚡</span>';
                                            }}
                                        />
                                    </div>
                                    <span style={{ fontSize: '11px', fontWeight: 600, color: '#e5e7eb' }}>
                                        {model.name}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Custom Tooltip Overlay */}
                {tooltipData && (
                    <div className="chart-tooltip-overlay" style={{ left: tooltipData.x }}>
                        <div className="tooltip-date">
                            {(() => {
                                const date = new Date(tooltipData.date);
                                const dateStr = date.toLocaleDateString('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                    year: 'numeric',
                                    timeZone: 'America/New_York'
                                });

                                const time = date.toLocaleTimeString('en-US', {
                                    hour: '2-digit',
                                    minute: '2-digit',
                                    hour12: false,
                                    timeZone: 'America/New_York'
                                });

                                return `${dateStr} ${time} EST`;
                            })()}
                        </div>
                        {tooltipData.data.map((item: any) => {
                            const isHovered = hoveredModelId === item.id;
                            return (
                                <div
                                    key={item.id}
                                    className={`tooltip-item ${isHovered ? 'hovered' : ''}`}
                                    style={{ color: item.color }}
                                >
                                    <span>{item.name}</span>
                                    <span>${item.currentValue?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};

// Helpers
function getModelColor(name: string): string {
    if (name.includes('GPT')) return '#10a37f';
    if (name.includes('Claude')) return '#d97757';
    if (name.includes('Gemini')) return '#4285f4';
    if (name.includes('Llama')) return '#0668e1';
    return '#9ca3af';
}

function extractProvider(name?: string): string {
    if (!name) return "Benchmark";
    const n = name.toLowerCase();
    if (n.includes("gpt") || n.includes("openai")) return "OpenAI";
    if (n.includes("claude") || n.includes("anthropic")) return "Anthropic";
    if (n.includes("llama")) return "Meta";
    if (n.includes("gemini")) return "Google";
    if (n.includes("kimi")) return "Moonshot";
    if (n.includes("qwen")) return "Qwen";
    if (n.includes("deepseek")) return "DeepSeek";
    if (n.includes("grok")) return "xAI";
    return "Benchmark";
}

// Compute timezone offset in minutes for a given date and zone (positive if zone ahead of UTC)
function getTimeZoneOffset(date: Date, timeZone: string): number {
    const dtf = new Intl.DateTimeFormat('en-US', {
        timeZone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
    });

    const parts = dtf.formatToParts(date);
    const values: any = {};
    for (const { type, value } of parts) {
        if (type !== 'literal') {
            values[type] = value;
        }
    }

    const asUTC = Date.UTC(
        Number(values.year),
        Number(values.month) - 1,
        Number(values.day),
        Number(values.hour),
        Number(values.minute),
        Number(values.second),
    );

    return (asUTC - date.getTime()) / 60000;
}

export default StockChart;
