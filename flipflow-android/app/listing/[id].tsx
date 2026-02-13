import { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  Alert,
  ActivityIndicator,
  StyleSheet,
} from "react-native";
import { useLocalSearchParams } from "expo-router";
import { getListing, enqueue, resurrectZombie } from "../../lib/api";
import type { ListingResponse } from "../../lib/types";
import StatusBadge from "../../components/StatusBadge";
import ActionButton from "../../components/ActionButton";
import ErrorBanner from "../../components/ErrorBanner";

export default function ListingDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [listing, setListing] = useState<ListingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [enqueuing, setEnqueuing] = useState(false);
  const [resurrecting, setResurrecting] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getListing(Number(id));
      setListing(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const handleEnqueue = async () => {
    if (!listing) return;
    setEnqueuing(true);
    try {
      const result = await enqueue({ listing_id: listing.id });
      Alert.alert("Enqueued", `Queue entry #${result.id} created`);
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setEnqueuing(false);
    }
  };

  const handleResurrect = async () => {
    if (!listing) return;
    setResurrecting(true);
    try {
      const result = await resurrectZombie(listing.id);
      if (result.success) {
        Alert.alert(
          "Resurrected",
          `New Item: ${result.new_item_id}\nCycle: ${result.cycle_number}`
        );
        load();
      } else {
        Alert.alert("Failed", result.error ?? "Unknown error");
      }
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setResurrecting(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#4fc3f7" size="large" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <ErrorBanner message={error} onRetry={load} />
      </View>
    );
  }

  if (!listing) return null;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <StatusBadge status={listing.status} />

      <Text style={styles.title}>
        {listing.title_sanitized ?? listing.title}
      </Text>

      <View style={styles.fields}>
        <Field label="ID" value={String(listing.id)} />
        <Field label="SKU" value={listing.sku} />
        <Field label="Original Title" value={listing.title} />
        <Field
          label="Purchase Price"
          value={`$${listing.purchase_price.toFixed(2)}`}
        />
        <Field
          label="List Price"
          value={`$${listing.list_price.toFixed(2)}`}
        />
        <Field label="Days Active" value={String(listing.days_active)} />
        <Field label="Total Views" value={String(listing.total_views)} />
        <Field
          label="Zombie Cycles"
          value={String(listing.zombie_cycle_count)}
        />
      </View>

      <View style={styles.actions}>
        <ActionButton
          title="Enqueue for Release"
          onPress={handleEnqueue}
          loading={enqueuing}
        />
        {listing.status === "zombie" && (
          <ActionButton
            title="Resurrect"
            onPress={handleResurrect}
            loading={resurrecting}
            variant="danger"
          />
        )}
      </View>
    </ScrollView>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <Text style={styles.fieldValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f0f23" },
  content: { padding: 16 },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#0f0f23",
  },
  title: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "700",
    marginTop: 12,
    marginBottom: 16,
  },
  fields: { marginBottom: 20 },
  field: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#1e1e3a",
  },
  fieldLabel: { color: "#999", fontSize: 13 },
  fieldValue: { color: "#ddd", fontSize: 13, fontWeight: "500" },
  actions: { gap: 8 },
});
