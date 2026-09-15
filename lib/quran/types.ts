export interface Ayah {
  global_ayah_number: number;
  surah_number: number;
  surah_name_ar: string;
  surah_name_transliteration: string;
  surah_name_bn: string | null;
  ayah_number: number;
  arabic: string;
  bangla: string;
}

export interface Surah {
  surah_number: number;
  name_ar: string;
  name_transliteration: string;
  name_bn: string | null;
  revelation_type: string;
  total_verses: number;
}
