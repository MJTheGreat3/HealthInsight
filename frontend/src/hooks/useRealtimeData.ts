/**
 * useRealtimeData Hook
 *
 * Provides easy subscription to real-time data updates for specific data types.
 * Automatically handles subscription/unsubscription and provides update callbacks.
 */

import { useEffect, useCallback, useRef } from "react";
import { useRealtime } from "../contexts/RealtimeContext";

interface DataUpdate {
  type: string;
  data: any;
  timestamp: string;
}

interface UseRealtimeDataOptions {
  /**
   * Array of data update types to listen for
   * e.g., ['report_uploaded', 'metrics_updated', 'profile_updated']
   */
  updateTypes?: string[];

  /**
   * Callback function called when relevant updates are received
   */
  onUpdate?: (update: DataUpdate) => void;

  /**
   * Whether to automatically trigger the callback for all updates (default: false)
   * If false, only updates matching updateTypes will trigger the callback
   */
  listenToAll?: boolean;
}

/**
 * Hook for subscribing to real-time data updates
 */
export function useRealtimeData(options: UseRealtimeDataOptions = {}) {
  const { subscribeToDataUpdates, isConnected, addNotification } =
    useRealtime();
  const { updateTypes = [], onUpdate, listenToAll = false } = options;
  const onUpdateRef = useRef(onUpdate);

  // Keep callback ref up to date
  useEffect(() => {
    onUpdateRef.current = onUpdate;
  }, [onUpdate]);

  // Subscribe to data updates
  useEffect(() => {
    const handleDataUpdate = (update: DataUpdate) => {
      // Check if we should handle this update
      const shouldHandle =
        listenToAll ||
        updateTypes.length === 0 ||
        updateTypes.includes(update.type);

      if (shouldHandle && onUpdateRef.current) {
        onUpdateRef.current(update);
      }
    };

    const unsubscribe = subscribeToDataUpdates(handleDataUpdate);
    return unsubscribe;
  }, [subscribeToDataUpdates, updateTypes, listenToAll]);

  // Utility function to manually trigger a notification
  const notify = useCallback(
    (notification: {
      type: "info" | "success" | "warning" | "error";
      title: string;
      message: string;
    }) => {
      addNotification(notification);
    },
    [addNotification]
  );

  return {
    isConnected,
    notify,
  };
}

/**
 * Hook specifically for report-related updates
 */
export function useRealtimeReports(
  onReportUpdate?: (update: DataUpdate) => void
) {
  return useRealtimeData({
    updateTypes: ["report_uploaded", "report_processed", "analysis_completed"],
    onUpdate: onReportUpdate,
  });
}

/**
 * Hook specifically for metrics-related updates
 */
export function useRealtimeMetrics(
  onMetricsUpdate?: (update: DataUpdate) => void
) {
  return useRealtimeData({
    updateTypes: [
      "metrics_updated",
      "tracked_metrics_changed",
      "dashboard_updated",
    ],
    onUpdate: onMetricsUpdate,
  });
}

/**
 * Hook specifically for profile-related updates
 */
export function useRealtimeProfile(
  onProfileUpdate?: (update: DataUpdate) => void
) {
  return useRealtimeData({
    updateTypes: ["profile_updated", "bio_data_changed", "preferences_updated"],
    onUpdate: onProfileUpdate,
  });
}

/**
 * Hook for hospital users to get patient-related updates
 */
export function useRealtimePatients(
  onPatientUpdate?: (update: DataUpdate) => void
) {
  return useRealtimeData({
    updateTypes: [
      "patient_registered",
      "patient_updated",
      "patient_report_uploaded",
    ],
    onUpdate: onPatientUpdate,
  });
}
