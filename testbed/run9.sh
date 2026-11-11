#!/usr/bin/env bash
# Run 9: name with only a home phone or address goes to the user (no check against).
cd "$(dirname "$0")"
run() { out=$1; shift; python standin_run.py --out "$out" "$@" > "$out.log" 2>&1; echo "$out exit $?" >> run9_status.txt; }
run run9_main   --corpus corpus/lakeside-dental         --name "Maria Lopez" --transcripts audio_main
run run9_hard   --corpus corpus-hard/lakeside-dental    --name "Maria Lopez" --transcripts audio_hard --choose-dob 1984-03-12
run run9_blind  --corpus blind/corpus/KestrelBay_Physio --name "Sarah Mitchell" --choose-dob 1983-09-22
run run9_demo   --corpus corpus-demo/lakeside-dental    --name "Maria Lopez" --transcripts audio_demo --choose-dob 1984-03-12
