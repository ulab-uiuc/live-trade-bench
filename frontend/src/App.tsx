import React, { useState, useEffect, useCallback, useRef } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import StockDashboard from "./components/StockDashboard";
import PolymarketDashboard from "./components/PolymarketDashboard";
import BitMEXDashboard from "./components/BitMEXDashboard";
import ForexDashboard from "./components/ForexDashboard";
import News from "./components/News";
import SocialMedia from "./components/SocialMedia";
import About from "./components/About";
import Navigation from "./components/Navigation";
import Footnote from "./components/Footnote";
import "./App.css";
import type { Model } from "./types";

// Global data interfaces
export interface NewsItem {
  id: string; // Add id for keying
  title: string;
  snippet: string; // Renamed from summary
  source: string;
  date: string; // Renamed from published_at
  link: string;
  tag?: string; // Renamed from stock_symbol and made optional
}

export interface SocialPost {
  id: string;
  title?: string; // Add title for Reddit posts
  platform: string;
  username: string;
  displayName: string;
  content: string;
  created_at: string;
  upvotes: number;
  num_comments: number;
  avatar: string;
  url: string; // Re-added url
  stock_symbols?: string[]; // Re-added stock_symbols
  tag?: string;
  question?: string; // Re-added question
}

function App() {
  // Add a ref to track if the initial fetch has been triggered
  const initialFetchComplete = useRef(false);

  // Global platform data - all managed in background
  const [modelsData, setModelsData] = useState<Model[]>([]);
  const [newsData, setNewsData] = useState<{
    stock: NewsItem[];
    polymarket: NewsItem[];
    bitmex: NewsItem[];
    forex: NewsItem[];
  }>({
    stock: [],
    polymarket: [],
    bitmex: [],
    forex: [],
  });
  const [socialData, setSocialData] = useState<{
    stock: SocialPost[];
    polymarket: SocialPost[];
    bitmex: SocialPost[];
    forex: SocialPost[];
  }>({
    stock: [],
    polymarket: [],
    bitmex: [],
    forex: [],
  });
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [views, setViews] = useState<number>(0);

  // Add a global loading state
  const [isLoading, setIsLoading] = useState(true);

  // Storing previous ranks for comparison
  const prevRanks = useRef<{ [key: string]: number }>({});

  // Last refresh timestamps for all data types
  const [modelsLastRefresh, setModelsLastRefresh] = useState<Date>(new Date());
  const [stockNextRefresh, setStockNextRefresh] = useState<Date | null>(null);
  const [polymarketNextRefresh, setPolymarketNextRefresh] =
    useState<Date | null>(null);
  const [forexNextRefresh, setForexNextRefresh] = useState<Date | null>(null);
  const [newsLastRefresh, setNewsLastRefresh] = useState<Date>(new Date());
  const [socialLastRefresh, setSocialLastRefresh] = useState<Date>(new Date());
  const [systemLastRefresh, setSystemLastRefresh] = useState<Date>(new Date());

  // Background data fetching functions
  const fetchNewsData = useCallback(async () => {
    try {
      console.log("🔄 Background fetching news data...");
      const [stockResponse, polymarketResponse, forexResponse] =
        await Promise.all([
          fetch("/api/news/stock?limit=500"),
          fetch("/api/news/polymarket?limit=500"),
          fetch("/api/news/forex?limit=500"),
        ]);

      const stockNews = stockResponse.ok ? await stockResponse.json() : [];
      const polymarketNews = polymarketResponse.ok
        ? await polymarketResponse.json()
        : [];
      const forexNews = forexResponse.ok ? await forexResponse.json() : [];

      // Fetch BitMEX news separately (optional endpoint)
      let bitmexNews: NewsItem[] = [];
      try {
        const bitmexResponse = await fetch("/api/news/bitmex?limit=500");
        if (bitmexResponse.ok) {
          bitmexNews = await bitmexResponse.json();
        }
      } catch {
        // BitMEX news endpoint optional, silently fail
      }

      setNewsData({
        stock: stockNews,
        polymarket: polymarketNews,
        bitmex: bitmexNews,
        forex: forexNews,
      });
      setNewsLastRefresh(new Date());
      console.log(
        `✅ Background news updated: ${stockNews.length} stock, ${polymarketNews.length} polymarket, ${bitmexNews.length} bitmex, ${forexNews.length} forex`
      );
    } catch (error) {
      console.error("❌ Background news fetch failed:", error);
    }
  }, []);

  const fetchSocialData = useCallback(async () => {
    try {
      console.log("🔄 Background fetching social data...");
      const [stockResponse, polymarketResponse, forexResponse] =
        await Promise.all([
          fetch("/api/social/stock?limit=500"),
          fetch("/api/social/polymarket?limit=500"),
          fetch("/api/social/forex?limit=500"),
        ]);

      console.log("DEBUG: 1. Raw API Response (Social)", {
        stock: stockResponse,
        polymarket: polymarketResponse,
        forex: forexResponse,
      });

      const stockPosts = stockResponse.ok ? await stockResponse.json() : [];
      const polymarketPosts = polymarketResponse.ok
        ? await polymarketResponse.json()
        : [];
      const forexPostsRaw = forexResponse.ok ? await forexResponse.json() : [];

      // Fetch BitMEX social separately (optional endpoint)
      let bitmexPosts: any[] = [];
      try {
        const bitmexResponse = await fetch("/api/social/bitmex?limit=500");
        if (bitmexResponse.ok) {
          bitmexPosts = await bitmexResponse.json();
        }
      } catch {
        // BitMEX social endpoint optional, silently fail
      }

      console.log("DEBUG: 2. Parsed JSON Data (Social)", {
        stockPosts,
        polymarketPosts,
        forexPostsRaw,
      });

      // Transform data to match expected format
      const transformStockPosts = stockPosts.map(
        (post: any, index: number) => ({
          ...post, // Keep original post data first
          id: post.id || `stock_${index}`,
          platform: post.platform || "Reddit",
          username: `u/${post.author}`,
          displayName: `u/${post.author}`,
          title: post.title, // Explicitly map title
          content: post.content || "", // Correctly map content, fallback to empty string
          created_at: post.created_at || "",
          upvotes: post.upvotes || 0,
          num_comments: post.num_comments || 0,
          avatar: "📈",
          tag: post.tag,
          stock_symbols: post.stock_symbols || [], // Ensure stock_symbols is an array
          url: post.url || "",
        })
      );

      const transformPolymarketPosts = polymarketPosts.map(
        (post: any, index: number) => ({
          ...post, // Keep original post data first
          id: post.id || `poly_${index}`,
          platform: post.platform || "Reddit",
          username: `u/${post.author}`,
          displayName: `u/${post.author}`,
          title: post.title, // Also map for polymarket in case it exists
          content: post.content || "", // Correctly map content, fallback to empty string
          created_at: post.created_at || "",
          upvotes: post.upvotes || 0,
          num_comments: post.num_comments || 0,
          avatar: "🎯",
          question: post.question,
          url: post.url || "",
        })
      );

      const transformBitmexPosts = bitmexPosts.map(
        (post: any, index: number) => ({
          ...post,
          id: post.id || `bitmex_${index}`,
          platform: post.platform || "Reddit",
          username: `u/${post.author}`,
          displayName: `u/${post.author}`,
          title: post.title,
          content: post.content || "",
          created_at: post.created_at || "",
          upvotes: post.upvotes || 0,
          num_comments: post.num_comments || 0,
          avatar: "₿",
          tag: post.tag,
          url: post.url || "",
        })
      );
      const transformForexPosts = forexPostsRaw.map(
        (post: any, index: number) => ({
          ...post,
          id: post.id || `forex_${index}`,
          platform: post.platform || "Reddit",
          username: `u/${post.author}`,
          displayName: `u/${post.author}`,
          title: post.title,
          content: post.content || "",
          created_at: post.created_at || "",
          upvotes: post.upvotes || 0,
          num_comments: post.num_comments || 0,
          avatar: "💱",
          tag: post.tag,
          url: post.url || "",
        })
      );

      setSocialData({
        stock: transformStockPosts,
        polymarket: transformPolymarketPosts,
        bitmex: transformBitmexPosts,
        forex: transformForexPosts,
      });
      setSocialLastRefresh(new Date());
      console.log(
        `✅ Background social updated: ${transformStockPosts.length} stock, ${transformPolymarketPosts.length} polymarket, ${transformBitmexPosts.length} bitmex, ${transformForexPosts.length} forex`
      );
    } catch (error) {
      console.error("❌ Background social fetch failed:", error);
    }
  }, []);

  const fetchModelsData = useCallback(async () => {
    try {
      console.log("🔄 Background fetching models data...");
      const [modelsResponse, nextUpdateResponse] = await Promise.all([
        fetch("/api/models/"),
        fetch("/api/schedule/next-price-update"),
      ]);

      if (modelsResponse.ok) {
        const currentModels: Model[] = await modelsResponse.json();

        // --- RANKING LOGIC ---
        // 1. Sort models by performance to determine rank
        const sortedModels = [...currentModels].sort(
          (a, b) => b.performance - a.performance
        );

        // 2. Create a map of model.id -> rank
        const newRanks: { [key: string]: number } = {};
        sortedModels.forEach((model, index) => {
          newRanks[model.id] = index + 1;
        });

        // 3. Calculate rank changes by comparing with previous ranks
        const newRankChanges: { [key: string]: number } = {};
        currentModels.forEach((model) => {
          const oldRank = prevRanks.current[model.id];
          const newRank = newRanks[model.id];
          if (oldRank && newRank) {
            // Correct logic: A lower rank number is better.
            // e.g., moving from rank 2 to 1 is a change of +1.
            newRankChanges[model.id] = oldRank - newRank;
          } else {
            newRankChanges[model.id] = 0; // No change for new models
          }
        });

        // 4. Add rank and rank_change to each model object
        const modelsWithRanks = currentModels.map((model) => ({
          ...model,
          rank: newRanks[model.id],
          rank_change: newRankChanges[model.id] || 0,
        }));

        // 5. Update state and store current ranks for the next fetch
        setModelsData(modelsWithRanks);
        setModelsLastRefresh(new Date());
        prevRanks.current = newRanks; // Store for next comparison

        console.log(
          `✅ Background models updated: ${currentModels.length} models with ranks`
        );
      }

      if (nextUpdateResponse.ok) {
        const scheduleData = await nextUpdateResponse.json();

        const parseTime = (value: any) => {
          if (typeof value !== "string") return null;
          const dt = new Date(value);
          return Number.isNaN(dt.getTime()) ? null : dt;
        };

        setStockNextRefresh(
          parseTime(scheduleData?.stock ?? scheduleData?.next_run_time)
        );
        setPolymarketNextRefresh(parseTime(scheduleData?.polymarket));
        setForexNextRefresh(parseTime(scheduleData?.forex));
      }
    } catch (error) {
      console.error("❌ Background models fetch failed:", error);
    }
  }, []);

  const fetchSystemStatus = useCallback(async () => {
    try {
      console.log("🔄 Background fetching system status...");
      const response = await fetch("/api/system");
      if (response.ok) {
        const status = await response.json();
        setSystemStatus(status);
        setSystemLastRefresh(new Date());
        console.log("✅ Background system status updated");
      }
    } catch (error) {
      console.error("❌ Background system status fetch failed:", error);
    }
  }, []);

  const fetchViews = useCallback(async () => {
    try {
      const baseUrl =
        process.env.NODE_ENV === "production" ? "" : "http://localhost:5001";

      const response = await fetch(`${baseUrl}/api/views`);
      if (response.ok) {
        const data = await response.json();
        setViews(data.views);
      }

      await fetch(`${baseUrl}/api/views`, { method: "POST" });

      const updatedResponse = await fetch(`${baseUrl}/api/views`);
      if (updatedResponse.ok) {
        const updatedData = await updatedResponse.json();
        setViews(updatedData.views);
      }
    } catch (error) {
      console.error("Failed to fetch views:", error);
    }
  }, []);

  // Parallel data fetching function
  const fetchAllDataInParallel = useCallback(async () => {
    console.log("🔄 Starting parallel data fetch...");
    const startTime = Date.now();

    try {
      // Execute all fetch functions in parallel
      await Promise.all([
        fetchModelsData(),
        fetchNewsData(),
        fetchSocialData(),
        fetchSystemStatus(),
        fetchViews(),
      ]);

      const elapsed = Date.now() - startTime;
      console.log(`✅ Parallel fetch completed in ${elapsed}ms`);
    } catch (error) {
      console.error("❌ Parallel fetch failed:", error);
    } finally {
      // Set loading to false after the first fetch completes
      if (initialFetchComplete.current) {
        setIsLoading(false);
      }
    }
  }, [fetchModelsData, fetchNewsData, fetchSocialData, fetchSystemStatus]);

  // Unified background data management
  useEffect(() => {
    // This effect should only run ONCE during the app's entire lifecycle
    if (initialFetchComplete.current) {
      console.log("↩️ Initial fetch already completed, skipping effect.");
      return;
    }
    initialFetchComplete.current = true;

    console.log(
      "🚀 Starting unified background data management for the first time..."
    );

    // Fetch all data immediately on app start in parallel
    fetchAllDataInParallel();

    // Smart parallel interval management
    // Group updates that can happen together to maximize parallel efficiency

    // High frequency: Models + System (every 1 minute for debugging)
    const highFreqInterval = setInterval(async () => {
      console.log("🔄 High frequency parallel update (1 min)...");
      await Promise.all([fetchModelsData(), fetchSystemStatus()]);
    }, 1 * 60 * 1000);

    // Medium frequency: News + Social (every 10 minutes, parallel)
    const lowFreqInterval = setInterval(async () => {
      console.log("🔄 Low frequency parallel update...");
      await Promise.all([fetchNewsData(), fetchSocialData()]);
    }, 10 * 60 * 1000);

    console.log("⏰ Smart parallel intervals set: High(1m), Medium(10m)");

    // Cleanup all intervals on unmount
    return () => {
      clearInterval(highFreqInterval);
      clearInterval(lowFreqInterval);
      console.log("🛑 All parallel intervals cleared");
    };
    // The dependency array is correct, but we've added a ref guard to prevent re-runs from HMR.
  }, [
    fetchAllDataInParallel,
    fetchModelsData,
    fetchNewsData,
    fetchSocialData,
    fetchSystemStatus,
    fetchViews,
  ]);

  return (
    <Router>
      <div className="App">
        <Navigation />
        <div className="main-content">
          <Routes>
            <Route
              path="/"
              element={
                <Dashboard
                  modelsData={modelsData}
                  modelsLastRefresh={modelsLastRefresh}
                  stockNextRefresh={stockNextRefresh || undefined}
                  polymarketNextRefresh={polymarketNextRefresh || undefined}
                  forexNextRefresh={forexNextRefresh || undefined}
                  systemStatus={systemStatus}
                  systemLastRefresh={systemLastRefresh}
                  views={views}
                />
              }
            />
            <Route
              path="/stocks"
              element={
                <StockDashboard
                  modelsData={modelsData}
                  modelsLastRefresh={modelsLastRefresh}
                  isLoading={isLoading}
                />
              }
            />
            <Route
              path="/polymarket"
              element={
                <PolymarketDashboard
                  modelsData={modelsData}
                  modelsLastRefresh={modelsLastRefresh}
                  isLoading={isLoading}
                />
              }
            />
            <Route
              path="/bitmex"
              element={
                <BitMEXDashboard
                  modelsData={modelsData}
                  modelsLastRefresh={modelsLastRefresh}
                  isLoading={isLoading}
                />
              }
            />
            <Route
              path="/forex"
              element={
                <ForexDashboard
                  modelsData={modelsData}
                  modelsLastRefresh={modelsLastRefresh}
                  isLoading={isLoading}
                />
              }
            />
            <Route
              path="/news"
              element={
                <News
                  newsData={newsData}
                  lastRefresh={newsLastRefresh}
                  isLoading={isLoading}
                />
              }
            />
            <Route
              path="/social"
              element={
                <SocialMedia
                  socialData={socialData}
                  lastRefresh={socialLastRefresh}
                  isLoading={isLoading}
                />
              }
            />
            <Route path="/about" element={<About />} />
          </Routes>
        </div>
        <Footnote />
      </div>
    </Router>
  );
}

export default App;
