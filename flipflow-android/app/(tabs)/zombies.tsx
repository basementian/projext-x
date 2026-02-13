import { useCallback, useState } from "react";
import {
  View,
  Text,
  FlatList,
  Alert,
  RefreshControl,
  StyleSheet,
} from "react-native";
import { useFocusEffect } from "expo-router";
import { scanZombies, resurrectZombie } from "../../lib/api";
import type { ZombieScanResult, ZombieReport } from "../../lib/types";
import ActionButton from "../../components/ActionButton";
import ErrorBanner from "../../components/ErrorBanner";
import StatCard from "../../components/StatCard";

export default function Zombies() {
  const [scan, setScan] = useState<ZombieScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [resurrecting, setResurrecting] = useState<number | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await scanZombies();
      setScan(data);
    } catch (e: any) {
      setError(e.message);
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

  const handleResurrect = async (zombie: ZombieReport) => {
    setResurrecting(zombie.listing_id);
    try {
      const result = await resurrectZombie(zombie.listing_id);
      if (result.success) {
        Alert.alert(
          "Resurrected",
          `SKU: ${result.sku}\nNew Item: ${result.new_item_id}\nCycle: ${result.cycle_number}`
        );
      } else {
        Alert.alert("Failed", result.error ?? "Unknown error");
      }
      load();
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setResurrecting(null);
    }
  };

  const renderZombie = ({ item }: { item: ZombieReport }) => (
    <View style={styles.card}>
      <View style={styles.row}>
        <Text style={styles.sku}>{item.sku}</Text>
        {item.should_purgatory && (
          <Text style={styles.purgatory}>PURGATORY</Text>
        )}
      </View>
      <Text style={styles.title} numberOfLines={1}>
        {item.title}
      </Text>
      <View style={styles.row}>
        <Text style={styles.meta}>{item.days_active}d active</Text>
        <Text style={styles.meta}>{item.total_views} views</Text>
        <Text style={styles.meta}>{item.watchers} watchers</Text>
        <Text style={styles.meta}>Cycle {item.zombie_cycle_count}</Text>
      </View>
      {item.current_price && (
        <Text style={styles.price}>${item.current_price.toFixed(2)}</Text>
      )}
      <ActionButton
        title={item.should_purgatory ? "In Purgatory" : "Resurrect"}
        onPress={() => handleResurrect(item)}
        loading={resurrecting === item.listing_id}
        disabled={item.should_purgatory}
        variant={item.should_purgatory ? "secondary" : "primary"}
      />
    </View>
  );

  return (
    <View style={styles.container}>
      {error && <ErrorBanner message={error} onRetry={load} />}

      {scan && (
        <View style={styles.stats}>
          <StatCard label="Scanned" value={scan.total_scanned} />
          <StatCard
            label="Zombies"
            value={scan.zombies_found}
            color="#f44336"
          />
          <StatCard
            label="Purgatory"
            value={scan.purgatory_candidates}
            color="#ff9800"
          />
        </View>
      )}

      <FlatList
        data={scan?.zombies ?? []}
        keyExtractor={(item) => String(item.listing_id)}
        renderItem={renderZombie}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        contentContainerStyle={{ padding: 16 }}
        ListEmptyComponent={
          <Text style={styles.empty}>No zombies detected</Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f0f23" },
  stats: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    padding: 16,
    paddingBottom: 0,
  },
  card: {
    backgroundColor: "#1e1e3a",
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: 6,
  },
  sku: { color: "#4fc3f7", fontSize: 13, fontWeight: "600" },
  purgatory: {
    color: "#ff9800",
    fontSize: 11,
    fontWeight: "700",
  },
  title: { color: "#ddd", fontSize: 14, marginVertical: 4 },
  meta: { color: "#999", fontSize: 11 },
  price: { color: "#4caf50", fontSize: 13, marginVertical: 4 },
  empty: { color: "#666", textAlign: "center", marginTop: 40 },
});
