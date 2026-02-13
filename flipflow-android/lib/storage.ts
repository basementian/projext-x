import AsyncStorage from "@react-native-async-storage/async-storage";

const API_URL_KEY = "flipflow_api_url";
const DEFAULT_API_URL = "http://192.168.1.2:8000/api/v1";

export async function getApiUrl(): Promise<string> {
  const url = await AsyncStorage.getItem(API_URL_KEY);
  return url ?? DEFAULT_API_URL;
}

export async function setApiUrl(url: string): Promise<void> {
  await AsyncStorage.setItem(API_URL_KEY, url);
}

export { DEFAULT_API_URL };
