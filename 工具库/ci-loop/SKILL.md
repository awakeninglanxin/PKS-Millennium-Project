---
name: ci-loop
description: "APK automatic build → install → verify → fix loop. When an APK build is pushed to GitHub Actions, this skill automates: wait for build, download APK, adb install on connected device, crash detection via logcat, structured crash analysis, source code fix, re-push. Use when the user says 'ci loop', 'auto fix APK', '自动修复APK', 'loop修复', 'build loop', or after any code change that should be verified on device. Supports up to 30 auto-fix iterations per session."
agent_created: true
---

# CI Loop — APK build → install → verify → fix

Automated APK build verification loop for the NLS Self-Balancing project at
`awakeninglanxin/NLS_self-balancing`.

## Trigger

Use this skill when:
- User says "ci loop", "自动修复APK", "loop修复", "build loop", "auto fix"
- After pushing code to GitHub and waiting for the Actions build
- When the NLS balance APK needs verification on a connected Android device

## Prerequisites

- `adb` in PATH (USB-connected Android device, USB debugging enabled)
- `gh` CLI authenticated (`gh auth status`)
- Repo: `awakeninglanxin/NLS_self-balancing`
- Script: `scripts/verify_apk.sh` must be chmod +x

## Loop Workflow (max 30 rounds)

### Round structure

```
1. Wait for GitHub Actions build → gh run list --limit 1
2. If build success → download APK → gh run download -n "NLS-Self-Balancing-APK"
3. Run verify_apk.sh → 4-layer check
4. If exit 0 → SUCCESS, stop loop
5. If exit 10 → read verify_fail_install.txt, fix build.gradle.kts / AndroidManifest.xml
6. If exit 13 → read verify_crash.txt, analyze crash, fix Kotlin source
7. git commit + push → back to step 1
```

### Step 1: Check Latest Build

```bash
# Get latest run ID
RUN_ID=$(gh run list --repo awakeninglanxin/NLS_self-balancing --limit 1 --json databaseId,status,conclusion --jq '.[0].databaseId')
CONCLUSION=$(gh run list --repo awakeninglanxin/NLS_self-balancing --limit 1 --json conclusion --jq '.[0].conclusion')

if [ "$CONCLUSION" = "failure" ]; then
  # Read build error log
  gh run view $RUN_ID --repo awakeninglanxin/NLS_self-balancing --log-failed
  # Analyze error, fix source, push
fi
```

### Step 2: Download APK

```bash
cd ~/Desktop
rm -f nls_balance.apk
gh run download $RUN_ID --repo awakeninglanxin/NLS_self-balancing --name "NLS-Self-Balancing-APK" --dir apk-tmp
mv apk-tmp/*.apk nls_balance.apk
rm -rf apk-tmp
```

### Step 3: Verify on Device

```bash
bash ~/.workbuddy/skills/ci-loop/scripts/verify_apk.sh ~/Desktop/nls_balance.apk
```

### Exit Code Reference

| Code | Meaning | Fix Action |
|:---:|------|------|
| 0 | All checks passed | STOP loop, report success |
| 10 | Install failed | Read `verify_fail_install.txt`, check AndroidManifest.xml, minSdk, permissions |
| 11/12 | Start failed | Read `am_start.log`, check exported activities, intent filters |
| 13 | Runtime crash | Read `verify_crash.txt`, map crash type to fix template |

### Crash Analysis (exit 13) — Fix Templates

These are the known crash patterns for NLS Self-Balancing APK:

| Crash Pattern | Root Cause | Fix |
|------|------|------|
| `InflateException` + `MaterialButton` | MaterialComponents theme with `<Button>` | Replace with `<TextView>` + `background` + `clickable=true` |
| `ClassNotFoundException` + custom View | Custom View in XML | Create View programmatically via `addView()` in Kotlin |
| `NoSuchMethodError` + View constructor | Missing `@JvmOverloads` | Add `@JvmOverloads constructor(context, attrs, defStyleAttr)` |
| `Color.parseColor` + "Unknown color" | 3-char hex like `#aaa` | Use 6-char `#aaaaaa` |
| `ConcurrentModificationException` | Thread safety of shared maps | Use `mapValues{}` deep copy before crossing thread boundary |
| `NullPointerException` + `findViewById` | View ID mismatch | Verify layout XML has corresponding `android:id` |

### Step 4: Fix and Push

After identifying the crash cause:
1. Read and edit the relevant Kotlin/XML file
2. Apply the fix template
3. Commit with descriptive message
4. Push to trigger new build

```bash
cd /d/AAA我的文件/nls_dynamic_balancer
git add -A
git commit -m "ci_loop round $ROUND: fix <what was fixed>"
git push
```

## Iron Rules (from hard-won experience)

1. **Never use `<Button>` with `backgroundTint` under `Theme.MaterialComponents`** — use `<TextView>` instead
2. **Never declare custom Views in XML** — use `FrameLayout` placeholder + `addView()` in code
3. **Custom View constructors need `@JvmOverloads`** — XML inflation calls 3-arg/4-arg constructors
4. **`Color.parseColor()` requires 6+ hex digits** — `#aaa` is illegal, use `#aaaaaa`
5. **Thread safety for mutable state** — `algoStats` is shared between IO and UI threads, use deep copy
6. **Single change per iteration** — from a known stable baseline, change one thing at a time

## Verification Script

Located at `scripts/verify_apk.sh`. Four-layer detection:

- **L1 Install**: `adb install -r -t`, captures `INSTALL_FAILED`
- **L2 Start**: `am start -W`, checks `Status: ok`
- **L3 Crash**: `adb logcat -b crash`, captures FATAL stack traces
- **L4 Alive**: `dumpsys window`, confirms Activity is in foreground
