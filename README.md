# 가치토라! ~폭주 교사 in High School~ (PSP) 비공식 한글패치

PSP 일본판 **ガチトラ！～暴れん坊教師 in High School～ (NPJH-50409)** 비공식 한국어 패치입니다. 이 저장소에는 제작 도구와 기술 문서만 있고, 패치 파일(xdelta)은 [Releases](../../releases)에서 받을 수 있습니다. 게임 원본·일본어 원문·번역 대본은 포함하지 않습니다.

## 적용 방법
1. 아래 해시와 일치하는 **원본 `.iso`** 를 준비합니다. (CSO·CHD 등으로 변환한 이미지에는 적용할 수 없습니다.)
   - PowerShell: `Get-FileHash -Algorithm MD5 -LiteralPath '.\Gachitora! Abarenbou Kyoushi in High School (Japan).iso'`
2. xdeltaUI 같은 도구로 원본에 `Gachitora_Abarenbou_Kyoushi_KO_v1.0.xdelta` 를 적용합니다.
   - 명령줄: `xdelta3 -d -s "Gachitora! Abarenbou Kyoushi in High School (Japan).iso" Gachitora_Abarenbou_Kyoushi_KO_v1.0.xdelta "Gachitora! Abarenbou Kyoushi in High School (Korean).iso"`
3. 만들어진 ISO를 PPSSPP 또는 커스텀 펌웨어에서 실행합니다.

| 항목 | 값 |
| --- | --- |
| 원본 ISO 크기 | 1,686,568,960 바이트 |
| 원본 ISO MD5 | `813aa8aeb9cbe8f8a6fbc6d709427c4a` |
| 원본 ISO SHA-256 | `f040b13625e89a8f67ffcb02b2b17c8b93eb512e6c7ed562e5a0e3f97b04b3f7` |
| xdelta SHA-256 | `0f5161947de8cdc99cd22b6dea5504403cd4dc3cfc135c8eabf15cdd06c893db` |
| 결과 ISO 크기 | 1,835,595,776 바이트 |
| 결과 ISO SHA-256 | `556eed82a0e6dcfe1a11a4f4d3c09ab9ee8dc505646ae9d26d5dff9cbdb38079` |

## 주의
- EBOOT를 복호화한 평문 ELF로 넣었기 때문에 **PPSSPP·커스텀 펌웨어 전용**입니다. 정품 펌웨어에서는 부팅되지 않습니다.
- **타이틀 메뉴의 「설치하기」 기능은 쓰지 마세요.** 원본의 설치용 데이터(INSDIR)는 암호화되어 있어 고칠 수 없으므로, 패치는 디스크의 평문 사본(INSTMP)을 읽도록 바꿨습니다.

## 한글화 내용
- 텍스트 24,108개(원문 약 50만 자): 이벤트 대사, 마을 NPC·고민 상담 대화, 전투 대사, 메뉴·시스템 메시지, 아이템·인물 소개·잡학, 미니게임(퀴즈·게시판·동영상 댓글 등), 스태프롤
- 실행 파일 문자열 약 230개 + 코드에 박힌 글자 85자: 조작 안내, 미션명, 장소명, 경매 문구, 주소록·낚시·대출 화면 항목 등
- 그림 글자 약 1,130장: 타이틀 로고, 부팅 경고문, 메뉴·버튼, 도감·평가표, 상점·지도·메이드 카페, 미니게임, 인물 소개 컷, 뉴스 자막·신문·피켓, 거리의 가게 간판·도로 표지판·안내판, 교실 표찰 등
- XMB 게임 제목
- 글꼴: 시스템 폰트(jpn0) 대신 디스크에 넣은 PGF를 읽도록 하고, 원본 글자에 나눔스퀘어네오 Bold로 한글 2,350자 추가

## 그대로 둔 것
- 실존 브랜드·작품 로고(서클K, sunkus, Right-on, 스테이크노돈, Tackle Berry, 단간론파 등)와 영어 문구
- 동영상, 음성
- 몇 픽셀밖에 안 되는 판독 불가능한 작은 글씨(벽보 본문, 서류, 자판기 라벨 등)
- 필드 이벤트 상단의 「스킵·정지」는 원판과 같이 버튼 아이콘 없이 글자만 표시됩니다.

## 검증 범위
PPSSPP에서 부팅, 경고 화면, 타이틀·메뉴, 오프닝 이벤트, 첫 필드(고급주택가·주택가)의 대사·간판·표지판까지 확인했습니다. 전체 플레이 검증은 하지 않았습니다.

## 문서
- [CHANGELOG.md](CHANGELOG.md) — 변경 기록
- [docs/TECHNICAL.md](docs/TECHNICAL.md) — 파일 형식과 한글화 방법
- [docs/BUILD.md](docs/BUILD.md) — 직접 빌드하는 방법
- [docs/FONT_CREDITS.md](docs/FONT_CREDITS.md) — 글꼴
- [RIGHTS.md](RIGHTS.md) — 권리 및 외부 자료
