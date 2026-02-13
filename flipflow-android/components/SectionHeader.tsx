import { View, Text, StyleSheet } from "react-native";

export default function SectionHeader({ title }: { title: string }) {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>{title}</Text>
      <View style={styles.line} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginTop: 20, marginBottom: 10 },
  text: { color: "#fff", fontSize: 16, fontWeight: "700", marginBottom: 4 },
  line: { height: 1, backgroundColor: "#333" },
});
