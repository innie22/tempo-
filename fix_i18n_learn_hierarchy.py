import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

# In vi:
# Replace:
#                     }
#                 }
#             },
#                 learn: {
# With:
#                     }
#                 },
#                 learn: {

old_vi_block = '''                        disrupted_routine: {
                            title: "Lối sống hằng ngày bị xáo trộn kéo dài",
                            usage: "Lịch ngủ bị đảo lộn, ăn uống thất thường và các thói quen hằng ngày bị xói mòn bởi căng thẳng liên miên."
                        }
                    }
                }
            },
                learn: {'''

new_vi_block = '''                        disrupted_routine: {
                            title: "Lối sống hằng ngày bị xáo trộn kéo dài",
                            usage: "Lịch ngủ bị đảo lộn, ăn uống thất thường và các thói quen hằng ngày bị xói mòn bởi căng thẳng liên miên."
                        }
                    }
                },
                learn: {'''

old_en_block = '''                        disrupted_routine: {
                            title: "Prolonged disrupted routine",
                            usage: "Sleep schedules overturned, eating becomes erratic, and everyday habits erode under sustained stress."
                        }
                    }
                }
            },
                learn: {'''

new_en_block = '''                        disrupted_routine: {
                            title: "Prolonged disrupted routine",
                            usage: "Sleep schedules overturned, eating becomes erratic, and everyday habits erode under sustained stress."
                        }
                    }
                },
                learn: {'''

# Also, where learn closes:
# Currently learn has its own closing brace:
#                         }
#                     }
#                 },
# We need to make sure the closing brace of community is at the end of learn!
# Let's inspect how learn ends in vi and en!

idx_vi_learn = text.find('learn: {')
idx_vi_cards = text.find('stress_loop:', idx_vi_learn)
idx_vi_learn_end = text.find('},', idx_vi_cards + 200)
print("VI learn end snippet:\n", text[idx_vi_learn_end-50:idx_vi_learn_end+150])

norm = text.replace('\r\n', '\n')
assert old_vi_block.replace('\r\n', '\n') in norm, "old_vi_block not found"
assert old_en_block.replace('\r\n', '\n') in norm, "old_en_block not found"

print("Both blocks found successfully!")
