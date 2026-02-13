import { Pressable, Text, ActivityIndicator, StyleSheet } from "react-native";

const VARIANTS: Record<string, string> = {
  primary: "#4fc3f7",
  danger: "#f44336",
  secondary: "#555",
};

interface Props {
  title: string;
  onPress: () => void;
  loading?: boolean;
  variant?: "primary" | "danger" | "secondary";
  disabled?: boolean;
}

export default function ActionButton({
  title,
  onPress,
  loading = false,
  variant = "primary",
  disabled = false,
}: Props) {
  const bg = VARIANTS[variant];
  return (
    <Pressable
      style={[styles.btn, { backgroundColor: bg }, disabled && styles.disabled]}
      onPress={onPress}
      disabled={loading || disabled}
    >
      {loading ? (
        <ActivityIndicator color="#fff" size="small" />
      ) : (
        <Text style={styles.text}>{title}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  btn: {
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 6,
    alignItems: "center",
    marginVertical: 4,
  },
  text: { color: "#fff", fontSize: 14, fontWeight: "600" },
  disabled: { opacity: 0.5 },
});
