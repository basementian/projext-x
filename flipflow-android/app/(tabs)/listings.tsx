import { useCallback, useState } from "react";
import {
  View,
  Text,
  TextInput,
  FlatList,
  Pressable,
  Alert,
  RefreshControl,
  StyleSheet,
} from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { getListings, createListing } from "../../lib/api";
import type { ListingResponse } from "../../lib/types";
import ListingCard from "../../components/ListingCard";
import ActionButton from "../../components/ActionButton";
import ErrorBanner from "../../components/ErrorBanner";

const FILTERS = ["all", "active", "draft", "zombie", "purgatory", "sold"];

export default function Listings() {
  const router = useRouter();
  const [listings, setListings] = useState<ListingResponse[]>([]);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);

  // Form fields
  const [sku, setSku] = useState("");
  const [title, setTitle] = useState("");
  const [purchasePrice, setPurchasePrice] = useState("");
  const [listPrice, setListPrice] = useState("");
  const [shippingCost, setShippingCost] = useState("");
  const [brand, setBrand] = useState("");
  const [model, setModel] = useState("");

  const load = useCallback(async () => {
    setError(null);
    try {
      const status = filter === "all" ? undefined : filter;
      const data = await getListings(status);
      setListings(data);
    } catch (e: any) {
      setError(e.message);
    }
  }, [filter]);

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

  const handleCreate = async () => {
    if (!sku || !title || !purchasePrice || !listPrice) {
      Alert.alert("Error", "SKU, Title, Purchase Price, and List Price are required");
      return;
    }
    setCreating(true);
    try {
      const result = await createListing({
        sku,
        title,
        purchase_price: parseFloat(purchasePrice),
        list_price: parseFloat(listPrice),
        shipping_cost: shippingCost ? parseFloat(shippingCost) : 0,
        brand: brand || undefined,
        model: model || undefined,
      });
      Alert.alert(
        "Listing Created",
        `SKU: ${result.sku}\nTitle: ${result.title_sanitized}\nProfit: $${result.profit.net_profit.toFixed(2)}\nMeets Floor: ${result.profit.meets_floor ? "Yes" : "No"}`
      );
      setSku("");
      setTitle("");
      setPurchasePrice("");
      setListPrice("");
      setShippingCost("");
      setBrand("");
      setModel("");
      setShowForm(false);
      load();
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setCreating(false);
    }
  };

  return (
    <View style={styles.container}>
      {error && <ErrorBanner message={error} onRetry={load} />}

      <Pressable
        style={styles.toggleBtn}
        onPress={() => setShowForm(!showForm)}
      >
        <Text style={styles.toggleText}>
          {showForm ? "Hide Form" : "+ New Listing"}
        </Text>
      </Pressable>

      {showForm && (
        <View style={styles.form}>
          <TextInput style={styles.input} placeholder="SKU" placeholderTextColor="#666" value={sku} onChangeText={setSku} />
          <TextInput style={styles.input} placeholder="Title" placeholderTextColor="#666" value={title} onChangeText={setTitle} />
          <View style={styles.row}>
            <TextInput style={[styles.input, styles.half]} placeholder="Purchase $" placeholderTextColor="#666" value={purchasePrice} onChangeText={setPurchasePrice} keyboardType="decimal-pad" />
            <TextInput style={[styles.input, styles.half]} placeholder="List $" placeholderTextColor="#666" value={listPrice} onChangeText={setListPrice} keyboardType="decimal-pad" />
          </View>
          <TextInput style={styles.input} placeholder="Shipping $ (optional)" placeholderTextColor="#666" value={shippingCost} onChangeText={setShippingCost} keyboardType="decimal-pad" />
          <View style={styles.row}>
            <TextInput style={[styles.input, styles.half]} placeholder="Brand" placeholderTextColor="#666" value={brand} onChangeText={setBrand} />
            <TextInput style={[styles.input, styles.half]} placeholder="Model" placeholderTextColor="#666" value={model} onChangeText={setModel} />
          </View>
          <ActionButton title="Add Listing" onPress={handleCreate} loading={creating} />
        </View>
      )}

      <View style={styles.filters}>
        {FILTERS.map((f) => (
          <Pressable
            key={f}
            style={[styles.pill, filter === f && styles.pillActive]}
            onPress={() => setFilter(f)}
          >
            <Text
              style={[styles.pillText, filter === f && styles.pillTextActive]}
            >
              {f}
            </Text>
          </Pressable>
        ))}
      </View>

      <FlatList
        data={listings}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => (
          <ListingCard
            listing={item}
            onPress={() =>
              router.push({ pathname: "/listing/[id]", params: { id: String(item.id) } })
            }
          />
        )}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        contentContainerStyle={{ padding: 16 }}
        ListEmptyComponent={
          <Text style={styles.empty}>No listings found</Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f0f23" },
  toggleBtn: { padding: 12, alignItems: "center" },
  toggleText: { color: "#4fc3f7", fontSize: 14, fontWeight: "600" },
  form: { padding: 16, backgroundColor: "#1a1a2e", marginHorizontal: 16, borderRadius: 8 },
  input: {
    backgroundColor: "#0f0f23",
    color: "#fff",
    padding: 10,
    borderRadius: 6,
    marginBottom: 8,
    fontSize: 14,
  },
  row: { flexDirection: "row", gap: 8 },
  half: { flex: 1 },
  filters: {
    flexDirection: "row",
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 6,
    flexWrap: "wrap",
  },
  pill: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 14,
    backgroundColor: "#1e1e3a",
  },
  pillActive: { backgroundColor: "#4fc3f7" },
  pillText: { color: "#999", fontSize: 12, textTransform: "capitalize" },
  pillTextActive: { color: "#000" },
  empty: { color: "#666", textAlign: "center", marginTop: 40 },
});
