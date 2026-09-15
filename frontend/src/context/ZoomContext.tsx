"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

interface ZoomContextType {
  zoomLevel: number;
  zoomIn: () => void;
  zoomOut: () => void;
  resetZoom: () => void;
  setZoom: (level: number) => void;
  canZoomIn: boolean;
  canZoomOut: boolean;
}

const MIN_ZOOM = 80;
const MAX_ZOOM = 150;
const ZOOM_STEP = 5;
const DEFAULT_ZOOM = 100;

const ZoomContext = createContext<ZoomContextType>({
  zoomLevel: DEFAULT_ZOOM,
  zoomIn: () => {},
  zoomOut: () => {},
  resetZoom: () => {},
  setZoom: () => {},
  canZoomIn: true,
  canZoomOut: true,
});

export const useZoom = () => useContext(ZoomContext);

export const ZoomProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [zoomLevel, setZoomLevel] = useState<number>(DEFAULT_ZOOM);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("trivium_global_zoom");
      if (saved) {
        const val = parseInt(saved, 10);
        if (!isNaN(val) && val >= MIN_ZOOM && val <= MAX_ZOOM) {
          setZoomLevel(val);
        }
      }
    } catch {
      // Ignora erro se localStorage inacessível
    }
  }, []);

  const updateZoom = useCallback((newLevel: number | ((prev: number) => number)) => {
    setZoomLevel((prev) => {
      const target = typeof newLevel === "function" ? newLevel(prev) : newLevel;
      const clamped = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, target));
      try {
        localStorage.setItem("trivium_global_zoom", clamped.toString());
      } catch {
        // ignora
      }
      return clamped;
    });
  }, []);

  const zoomIn = useCallback(() => {
    updateZoom((prev) => prev + ZOOM_STEP);
  }, [updateZoom]);

  const zoomOut = useCallback(() => {
    updateZoom((prev) => prev - ZOOM_STEP);
  }, [updateZoom]);

  const resetZoom = useCallback(() => {
    updateZoom(DEFAULT_ZOOM);
  }, [updateZoom]);

  const setZoom = useCallback((val: number) => {
    updateZoom(val);
  }, [updateZoom]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        if (e.key === "+" || e.key === "=" || e.key === "Add") {
          e.preventDefault();
          zoomIn();
        } else if (e.key === "-" || e.key === "_" || e.key === "Subtract") {
          e.preventDefault();
          zoomOut();
        } else if (e.key === "0" || e.key === "NumPad0") {
          e.preventDefault();
          resetZoom();
        }
      }
    };

    const handleWheel = (e: WheelEvent) => {
      // Se houver uma modal/tela cheia ativa (data-trivium-modal="true"), permitir scroll natural sem zoom de fundo
      const target = e.target as HTMLElement | null;
      if (target?.closest('[data-trivium-modal="true"]') || document.querySelector('[data-trivium-modal="true"]')) {
        return;
      }

      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        if (e.deltaY < 0) {
          zoomIn();
        } else if (e.deltaY > 0) {
          zoomOut();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown, { passive: false });
    window.addEventListener("wheel", handleWheel, { passive: false });

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("wheel", handleWheel);
    };
  }, [zoomIn, zoomOut, resetZoom]);

  const value: ZoomContextType = {
    zoomLevel,
    zoomIn,
    zoomOut,
    resetZoom,
    setZoom,
    canZoomIn: zoomLevel < MAX_ZOOM,
    canZoomOut: zoomLevel > MIN_ZOOM,
  };

  return (
    <ZoomContext.Provider value={value}>
      <div
        id="trivium-zoom-root"
        style={{ zoom: `${zoomLevel}%` }}
        className="min-h-screen transition-[zoom] duration-150 origin-top"
      >
        {children}
      </div>
    </ZoomContext.Provider>
  );
};