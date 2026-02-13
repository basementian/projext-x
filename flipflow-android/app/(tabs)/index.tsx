import { useCallback, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  StyleSheet,
} from "react-native";
import { useFocusEffect } from "expo-router";
import { checkHealth, getListings, getQueueStatus } from "../../lib/api";
import type { ListingResponse, QueueStatusResponse } from "../../lib/types";
import StatCard from "../../components/StatCard";
import ErrorBanner from "../../components/ErrorBanner";

export default function Dashboard() {
  const [connected, setConnected] = useState<boolean | null>(null);
  const [listings, setListings] = useState<ListingResponse[]>([]);
  const [queue, setQueue] = useState<QueueStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [health, listingsData, queueData] = await Promise.all([
        checkHealth().catch(() => null),
        getListings().catch(() => []),
        getQueueStatus().catch(() => null),
      ]);
      setConnected(health?.status === "ok");
      setListings(listingsData);
      setQueue(queueData);
    } catch (e: any) {
      setError(e.message);
      setConnected(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const count = (status: string) =>
    listings.filter((l) => l.status === status).length;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {error && <ErrorBanner message={error} onRetry={load} />}

      <View style={styles.statusRow}>
        <View
          style={[
            styles.dot,
            {
              backgroundColor:
                connected === null ? "#888" : connected ? "#4caf50" : "#f44336",
            },
          ]}
        />
        <Text style={styles.statusText}>
          {connected === null
            ? "Checking..."
            : connected
              ? "Connected"
              : "Disconnected"}
        </Text>
      </View>

      <Text style={styles.section}>Listings</Text>
      <View style={styles.grid}>
        <StatCard label="Total" value={listings.length} />
        <StatCard label="Active" value={count("active")} color="#4caf50" />
        <StatCard label="Zombies" value={count("zombie")} color="#f44336" />
        <StatCard label="Draft" value={count("draft")} />
        <StatCard label="Sold" value={count("sold")} color="#9c27b0" />
        <StatCard
          label="Purgatory"
          value={count("purgatory")}
          color="#ff9800"
        />
      </View>

      {queue && (
        <>
          <Text style={styles.section}>Queue</Text>
          <View style={styles.grid}>
            <StatCard label="Pending" value={queue.pending} />
            <StatCard label="Released Today" value={queue.released_today} />
            <StatCard label="Failed" value={queue.failed} color="#f44336" />
            <StatCard
              label="Surge Window"
              value={queue.surge_window_active ? "ACTIVE" : "Inactive"}
              color={queue.surge_window_active ? "#4caf50" : "#888"}
            />
          </View>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f0f23" },
  content: { padding: 16 },
  statusRow: { flexDirection: "row", alignItems: "center", marginBottom: 16 },
  dot: { width: 10, height: 10, borderRadius: 5, marginRight: 8 },
  statusText: { color: "#ddd", fontSize: 14 },
  section: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "700",
    marginBottom: 10,
    marginTop: 10,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
});
