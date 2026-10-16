#!/bin/bash
PY="C:/Users/Thinkpad/AppData/Local/Programs/Python/Python310/python.exe"
SK="../../skills/global"
run() {
  echo "===== $1 ====="
  (cd 篇章词汇_产出 && "$PY" "$SK/student-vocab-cards/scripts/student_cards.py" --file "../篇章文本_U7_U12/$2" --out "$1_学生卡" 2>&1 | tail -1)
  (cd 篇章词汇_产出 && "$PY" "$SK/teacher-vocab-prep/scripts/teacher_prep.py" --file "../篇章文本_U7_U12/$2" --out "$1_备课本" 2>&1 | tail -1)
  (cd 篇章词汇_产出 && "$PY" "$SK/british-phonetics/scripts/phonetics.py" --file "../篇章文本_U7_U12/$2" --out "$1_语音卡" --voice youdao --no-tts 2>&1 | tail -1)
}
run u9_p085_kitchenkids "Unit9_p085_Kitchen Kids.txt"
run u9_p087_cooking "Unit9_p087_Cooking.txt"
run u9_p088_inarestaurant "Unit9_p088_In a restaurant.txt"
run u9_p090_offeringhelp "Unit9_p090_Offering and asking for help.txt"
run u10_p092_firstwomaninspace "Unit10_p092_She was the first woman in space.txt"
run u10_p095_prizegiving "Unit10_p095_A prize-giving at school.txt"
run u10_p096_sportsachievers "Unit10_p096_Sports achievers.txt"
run u10_p099_statues "Unit10_p099_Statues around the world.txt"
run u11_p102_dolphins "Unit11_p102_Dolphins to the rescue.txt"
run u11_p105_joshsholiday "Unit11_p105_Josh's holiday.txt"
run u11_p106_extinctanimals "Unit11_p106_Extinct animals.txt"
run u11_p108_sequencing "Unit11_p108_Sequencing a story.txt"
echo ALL_DONE_C
