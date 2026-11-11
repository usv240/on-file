#!/usr/bin/env bash
cd "$(dirname "$0")"
run() { out=$1; shift; python standin_run.py --out "$out" "$@" > "$out.log" 2>&1; echo "$out exit $?" >> run9_status.txt; }
run run9_blind        --corpus blind/corpus/KestrelBay_Physio --name "Sarah Mitchell" --choose-dob 1983-09-22
run run9_main_stress  --corpus corpus/lakeside-dental         --name "Maria Lopez" --transcripts audio_main --topk 10 --snippet-check
run run9_hard_stress  --corpus corpus-hard/lakeside-dental    --name "Maria Lopez" --transcripts audio_hard --choose-dob 1984-03-12 --topk 10 --snippet-check
