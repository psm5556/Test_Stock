import { NextResponse } from 'next/server';

/**
 * 서버 환경변수 설정 여부를 클라이언트에 노출합니다.
 * 실제 값은 반환하지 않습니다.
 */
export async function GET() {
  return NextResponse.json({
    hasGoogleSheetId: !!process.env.GOOGLE_SHEET_ID,
    googleSheetName: process.env.GOOGLE_SHEET_NAME ?? '',
  });
}
