# CLI Code 💻🚀

Nowoczesny, szybki i funkcjonalny edytor kodu w terminalu (Linux TUI Code Editor).

## 🌟 Funkcje

- **Drzewo plików projektu** po lewej stronie z filtrowaniem i natychmiastowym otwieraniem plików.
- **Górny pasek informacyjny**:
  - Nazwa projektu i katalogu
  - Repozytorium Git i aktywna gałąź (ze statusem zmian dirty/clean `*`)
  - Aktywny plik i wskaźnik niezapisanych zmian `●`
  - Bieżący język programowania
  - Tryb edytora (`NORMAL` / `EDIT`)
- **Dolny pasek paneli (`Spacja + t`)**:
  - `Terminal`: wbudowana interaktywna konsola powłoki do wykonywania poleceń
  - `Output`: strumień wyjściowy uruchamianych zadań i projektów
  - `Debug Console`: logi i historia zdarzeń
  - `Błędy / Problems`: tabela z błędami i ostrzeżeniami lintera/kompilatora; kliknięcie przenosi kursor prosto do linii błędu!
- **Wybór języka (`Spacja + l`)**:
  - Obsługa Python, Dart / Flutter, JavaScript, TypeScript, Rust, Go, C/C++, Bash, JSON, YAML, TOML i innych.
  - Automatyczna analiza kodu przez zainstalowane narzędzia systemowe (`dart analyze`, `python3`, `ruff`, `gcc`, itp.).
- **Uruchamianie projektu (`Spacja + r`)**:
  - Inteligentne wykrywanie projektów:
    - **Flutter**: `flutter run`, `flutter run -d linux`, `flutter run -d chrome`, `flutter run --dart-define=FLAGA123=true`, `flutter test`, `flutter pub get`
    - **Python**: `python3 <plik>`, `pytest`, `python3 main.py`
    - **Node.js**: skrypty z `package.json` (`npm start`, `npm run dev`, `npm test`)
    - **Rust**: `cargo run`, `cargo test`
    - **Go**: `go run .`, `go test`
    - Dowolna własna komenda i flagi.
- **Szybkie otwieranie plików (`Spacja + p` / `Ctrl + p`)**:
  - Wyszukiwarka plików w projekcie z fuzzy searching.
- **Tworzenie nowych plików (`Spacja + n`)**.
- **Zapisywanie (`Spacja + w` / `Ctrl + s`)**.
- **Pomoc i skróty (`Spacja + h` / `F1`)**.

---

## ⌨️ Skróty klawiszowe

| Skrót | Akcja |
|---|---|
| `Spacja + l` | Menu wyboru języka |
| `Spacja + r` | Menu uruchomienia projektu |
| `Spacja + t` | Przełączanie paneli dolnych (Terminal, Output, Debug, Błędy) |
| `Spacja + p` | Szybkie szukanie i otwieranie plików |
| `Spacja + w` | Zapisz plik |
| `Spacja + n` | Nowy plik |
| `Spacja + b` | Pokaż / ukryj pasek boczny z plikami |
| `Spacja + h` / `F1` | Okno pomocy ze skrótami |
| `Ctrl + S` | Zapisz plik |
| `Ctrl + P` | Szukaj pliku |
| `Ctrl + B` | Przełącz pasek boczny |
| `Ctrl + T` | Przełącz panel dolny |
| `Ctrl + Q` | Wyjdź z edytora |
| `Esc` | Powrót do trybu NORMAL |
| `i` / `Enter` | Przejście do trybu edycji (EDIT) |

---

## 🚀 Uruchomienie

Możesz uruchomić edytor z dowolnego katalogu na dwa sposoby:
```bash
cli code
# lub
clicode
```

Możesz też podać konkretny folder lub plik:
```bash
cli code /sciezka/do/projektu
# lub
cli code main.py
```
