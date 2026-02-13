import { View, Text, StyleSheet } from "react-native";

const COLORS: Record<string, string> = {
  active: "#4caf50",
  draft: "#888",
  zombie: "#f44336",
  purgatory: "#ff9800",
  queued: "#2196f3",
  sold: "#9c27b0",
  ended: "#555",
};

export default function StatusBadge({ status }: { status: string }) {
  const bg = COLORS[status] ?? "#888";
  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <Text style={styles.text}>{status}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    alignSelf: "flex-start",
  },
  text: {
    color: "#fff",
    fontSize: 11,
    fontWeight: "700",
    textTransform: "uppercase",
  },
});
