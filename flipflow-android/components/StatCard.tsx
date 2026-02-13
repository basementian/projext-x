import { View, Text, StyleSheet } from "react-native";

interface Props {
  label: string;
  value: string | number;
  color?: string;
}

export default function StatCard({ label, value, color = "#4fc3f7" }: Props) {
  return (
    <View style={styles.card}>
      <Text style={[styles.value, { color }]}>{value}</Text>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#1e1e3a",
    borderRadius: 8,
    padding: 14,
    width: "48%",
    marginBottom: 10,
    alignItems: "center",
  },
  value: { fontSize: 28, fontWeight: "700" },
  label: { color: "#999", fontSize: 12, marginTop: 4 },
});
