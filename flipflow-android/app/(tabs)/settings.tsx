import { useEffect, useState } from "react";
import { View, Text, TextInput, Alert, StyleSheet } from "react-native";
import { getApiUrl, setApiUrl, DEFAULT_API_URL } from "../../lib/storage";
import { checkHealth } from "../../lib/api";
import ActionButton from "../../components/ActionButton";

export default function Settings() {
  const [url, setUrl] = useState("");
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    getApiUrl().then(setUrl);
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await setApiUrl(url.trim());
      Alert.alert("Saved", "API URL updated");
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const health = await checkHealth();
      Alert.alert(
        "Connected",
        `Service: ${health.service}\nVersion: ${health.version}\nStatus: ${health.status}`
      );
    } catch (e: any) {
      Alert.alert("Connection Failed", e.message);
    } finally {
      setTesting(false);
    }
  };

  const handleReset = () => {
    setUrl(DEFAULT_API_URL);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>API Base URL</Text>
      <TextInput
        style={styles.input}
        value={url}
        onChangeText={setUrl}
        placeholder="http://10.0.2.2:8000/api/v1"
        placeholderTextColor="#666"
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="url"
      />

      <View style={styles.btnRow}>
        <ActionButton title="Save" onPress={handleSave} loading={saving} />
        <ActionButton
          title="Test Connection"
          onPress={handleTest}
          loading={testing}
          variant="secondary"
        />
      </View>

      <ActionButton
        title="Reset to Default"
        onPress={handleReset}
        variant="secondary"
      />

      <View style={styles.info}>
        <Text style={styles.infoTitle}>Connection Guide</Text>
        <Text style={styles.infoText}>
          Android Emulator: http://10.0.2.2:8000/api/v1
        </Text>
        <Text style={styles.infoText}>
          Physical Device (same WiFi): http://YOUR_LAN_IP:8000/api/v1
        </Text>
        <Text style={styles.infoText}>
          Remote Server: https://your-server.com/api/v1
        </Text>
      </View>

      <Text style={styles.version}>FlipFlow v1.0.0</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f0f23", padding: 16 },
  label: { color: "#fff", fontSize: 14, fontWeight: "600", marginBottom: 8 },
  input: {
    backgroundColor: "#1e1e3a",
    color: "#fff",
    padding: 12,
    borderRadius: 6,
    fontSize: 14,
    marginBottom: 12,
  },
  btnRow: { flexDirection: "row", gap: 8, marginBottom: 8 },
  info: {
    backgroundColor: "#1e1e3a",
    borderRadius: 8,
    padding: 14,
    marginTop: 24,
  },
  infoTitle: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 8,
  },
  infoText: { color: "#999", fontSize: 12, marginBottom: 4 },
  version: { color: "#555", textAlign: "center", marginTop: 30, fontSize: 12 },
});
