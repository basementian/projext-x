import { useState } from "react";
import { View, Text, ScrollView, Alert, StyleSheet } from "react-native";
import {
  getQueueStatus,
  releaseBatch,
  previewRepricing,
  runRepricing,
  previewRelists,
  runRelists,
  scanOffers,
} from "../../lib/api";
import type {
  QueueStatusResponse,
  RepricerResult,
  RelisterCandidate,
  RelisterResult,
  OfferScanResult,
} from "../../lib/types";
import SectionHeader from "../../components/SectionHeader";
import ActionButton from "../../components/ActionButton";
import StatCard from "../../components/StatCard";

export default function Tools() {
  // Queue
  const [queue, setQueue] = useState<QueueStatusResponse | null>(null);
  const [queueLoading, setQueueLoading] = useState(false);
  const [releaseLoading, setReleaseLoading] = useState(false);

  // Repricer
  const [reprice, setReprice] = useState<RepricerResult | null>(null);
  const [repriceLoading, setRepriceLoading] = useState(false);
  const [repriceRunLoading, setRepriceRunLoading] = useState(false);

  // Relister
  const [relistCandidates, setRelistCandidates] = useState<RelisterCandidate[] | null>(null);
  const [relistResult, setRelistResult] = useState<RelisterResult | null>(null);
  const [relistPreviewLoading, setRelistPreviewLoading] = useState(false);
  const [relistRunLoading, setRelistRunLoading] = useState(false);

  // Offers
  const [offerResult, setOfferResult] = useState<OfferScanResult | null>(null);
  const [offerLoading, setOfferLoading] = useState(false);

  // === Queue ===
  const loadQueue = async () => {
    setQueueLoading(true);
    try {
      setQueue(await getQueueStatus());
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setQueueLoading(false);
    }
  };

  const handleRelease = async (dryRun: boolean) => {
    setReleaseLoading(true);
    try {
      const r = await releaseBatch(dryRun);
      Alert.alert(
        dryRun ? "Dry Run" : "Released",
        `Released: ${r.released}\nSurge Active: ${r.surge_window_active ? "Yes" : "No"}`
      );
      loadQueue();
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setReleaseLoading(false);
    }
  };

  // === Repricer ===
  const handleRepricePreview = async () => {
    setRepriceLoading(true);
    try {
      setReprice(await previewRepricing());
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setRepriceLoading(false);
    }
  };

  const handleRepriceRun = async () => {
    setRepriceRunLoading(true);
    try {
      const r = await runRepricing();
      setReprice(r);
      Alert.alert("Repriced", `${r.repriced} listings repriced, ${r.skipped} skipped`);
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setRepriceRunLoading(false);
    }
  };

  // === Relister ===
  const handleRelistPreview = async () => {
    setRelistPreviewLoading(true);
    try {
      setRelistCandidates(await previewRelists());
      setRelistResult(null);
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setRelistPreviewLoading(false);
    }
  };

  const handleRelistRun = async () => {
    setRelistRunLoading(true);
    try {
      const r = await runRelists();
      setRelistResult(r);
      Alert.alert("Relisted", `${r.relisted} relisted, ${r.skipped} skipped, ${r.errors} errors`);
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setRelistRunLoading(false);
    }
  };

  // === Offers ===
  const handleOfferScan = async () => {
    setOfferLoading(true);
    try {
      const r = await scanOffers();
      setOfferResult(r);
      Alert.alert("Offers Sent", `${r.offers_sent} offers sent, ${r.errors} errors`);
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setOfferLoading(false);
    }
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
    >
      {/* Queue */}
      <SectionHeader title="Queue Management" />
      <ActionButton title="Load Queue Status" onPress={loadQueue} loading={queueLoading} />
      {queue && (
        <View style={styles.stats}>
          <StatCard label="Pending" value={queue.pending} />
          <StatCard label="Released" value={queue.released_today} />
          <StatCard label="Failed" value={queue.failed} color="#f44336" />
          <StatCard
            label="Surge"
            value={queue.surge_window_active ? "ON" : "OFF"}
            color={queue.surge_window_active ? "#4caf50" : "#888"}
          />
        </View>
      )}
      <View style={styles.btnRow}>
        <ActionButton title="Release Batch" onPress={() => handleRelease(false)} loading={releaseLoading} />
        <ActionButton title="Dry Run" onPress={() => handleRelease(true)} variant="secondary" />
      </View>

      {/* Repricer */}
      <SectionHeader title="Graduated Repricer" />
      <View style={styles.btnRow}>
        <ActionButton title="Preview" onPress={handleRepricePreview} loading={repriceLoading} />
        <ActionButton title="Run Repricing" onPress={handleRepriceRun} loading={repriceRunLoading} variant="danger" />
      </View>
      {reprice && (
        <View style={styles.resultBox}>
          <Text style={styles.resultText}>
            Scanned: {reprice.total_scanned} | Repriced: {reprice.repriced} | Skipped: {reprice.skipped}
          </Text>
          {reprice.details.map((d, i) => (
            <Text key={i} style={styles.detailText}>
              {d.sku}: ${d.old_price.toFixed(2)} → ${d.new_price.toFixed(2)} (-{d.percent_off}% step {d.step})
            </Text>
          ))}
        </View>
      )}

      {/* Relister */}
      <SectionHeader title="Auto Relister" />
      <View style={styles.btnRow}>
        <ActionButton title="Preview" onPress={handleRelistPreview} loading={relistPreviewLoading} />
        <ActionButton title="Run Relists" onPress={handleRelistRun} loading={relistRunLoading} variant="danger" />
      </View>
      {relistCandidates && !relistResult && (
        <View style={styles.resultBox}>
          <Text style={styles.resultText}>{relistCandidates.length} candidates</Text>
          {relistCandidates.map((c, i) => (
            <Text key={i} style={styles.detailText}>
              {c.sku}: {c.days_active}d, {c.total_views} views, ${c.current_price.toFixed(2)}
            </Text>
          ))}
        </View>
      )}
      {relistResult && (
        <View style={styles.resultBox}>
          <Text style={styles.resultText}>
            Relisted: {relistResult.relisted} | Skipped: {relistResult.skipped} | Errors: {relistResult.errors}
          </Text>
        </View>
      )}

      {/* Offers */}
      <SectionHeader title="Offer Sniper" />
      <ActionButton title="Scan & Send Offers" onPress={handleOfferScan} loading={offerLoading} />
      {offerResult && (
        <View style={styles.resultBox}>
          <Text style={styles.resultText}>
            Checked: {offerResult.listings_checked} | Sent: {offerResult.offers_sent} | Errors: {offerResult.errors}
          </Text>
          {offerResult.details.map((d, i) => (
            <Text key={i} style={styles.detailText}>
              {d.sku} → {d.buyer_id}: ${d.offer_price.toFixed(2)} (-{d.discount_percent.toFixed(0)}%)
            </Text>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f0f23" },
  content: { padding: 16, paddingBottom: 40 },
  stats: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    marginTop: 8,
  },
  btnRow: { flexDirection: "row", gap: 8, marginTop: 4 },
  resultBox: {
    backgroundColor: "#1e1e3a",
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  resultText: { color: "#ddd", fontSize: 13, marginBottom: 4 },
  detailText: { color: "#999", fontSize: 12, marginTop: 2 },
});
