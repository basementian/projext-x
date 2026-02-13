import { View, Text, Pressable, StyleSheet } from "react-native";
import type { ListingResponse } from "../lib/types";
import StatusBadge from "./StatusBadge";

interface Props {
  listing: ListingResponse;
  onPress: () => void;
}

export default function ListingCard({ listing, onPress }: Props) {
  return (
    <Pressable style={styles.card} onPress={onPress}>
      <View style={styles.row}>
        <Text style={styles.sku}>{listing.sku}</Text>
        <StatusBadge status={listing.status} />
      </View>
      <Text style={styles.title} numberOfLines={1}>
        {listing.title_sanitized ?? listing.title}
      </Text>
      <View style={styles.row}>
        <Text style={styles.meta}>${listing.list_price.toFixed(2)}</Text>
        <Text style={styles.meta}>{listing.days_active}d</Text>
        <Text style={styles.meta}>{listing.total_views} views</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
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
  },
  sku: { color: "#4fc3f7", fontSize: 13, fontWeight: "600" },
  title: { color: "#ddd", fontSize: 14, marginVertical: 4 },
  meta: { color: "#999", fontSize: 12 },
});
