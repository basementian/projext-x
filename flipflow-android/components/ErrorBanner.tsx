import { View, Text, Pressable, StyleSheet } from "react-native";

interface Props {
  message: string;
  onRetry?: () => void;
}

export default function ErrorBanner({ message, onRetry }: Props) {
  return (
    <View style={styles.banner}>
      <Text style={styles.text}>{message}</Text>
      {onRetry && (
        <Pressable onPress={onRetry}>
          <Text style={styles.retry}>Retry</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: "#b71c1c",
    padding: 10,
    borderRadius: 6,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  text: { color: "#fff", fontSize: 13, flex: 1 },
  retry: { color: "#fff", fontWeight: "700", marginLeft: 10, fontSize: 13 },
});
