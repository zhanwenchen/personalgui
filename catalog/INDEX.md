# PersonalGUI Task Catalog — Index

**110 candidate tasks** across 10 life domains — **all 110 have a runnable `build_*_task()` builder** in [`src/personalgui/tasks/`](../src/personalgui/tasks/), each verified solvable by an oracle test. 105 were expressible with the 14 original mock apps; 5 needed a small new app surface (MockInvitePhotoApp / MockFileShareApp / MockFileDropApp / MockProfilePhotoApp and an enrollment mode on MockAuthenticatorApp), now added.

Generated from task-doc frontmatter by `scripts/build_catalog_index.py`. See [README.md](README.md) for the schema and metric taxonomy. **★** in the *Built* column = registered + oracle-verified.

## Metric coverage

| Primary metric | Tasks |
| --- | --- |
| handoff_correctness | 45 |
| source_of_truth | 20 |
| boundary_adherence | 15 |
| clarification_quality | 12 |
| minimal_transfer | 11 |
| routing_accuracy | 6 |
| global_success | 1 |

## Finance & expenses  (`finance_expenses/`)

| id | Title | Primary metric | Envs | Diff | code_ready | Built |
| --- | --- | --- | --- | --- | --- | --- |
| [fin_01](finance_expenses/fin_01_taxi-receipt-expense.md) | Taxi receipt amount to desktop expense report | handoff_correctness | android_phone, windows_desktop | 2 | yes | ★ |
| [fin_02](finance_expenses/fin_02_invoice-payment-reference.md) | Pay invoice using emailed payment reference | handoff_correctness | windows_desktop | 3 | yes | ★ |
| [fin_03](finance_expenses/fin_03_reconcile-authoritative-charge.md) | Reconcile charge against authoritative bank statement | source_of_truth | windows_desktop | 3 | yes | ★ |
| [fin_04](finance_expenses/fin_04_transfer-2fa-code.md) | Money transfer needing phone 2FA code on desktop bank form | handoff_correctness | android_phone, windows_desktop | 3 | yes | ★ |
| [fin_05](finance_expenses/fin_05_split-bill-total-only.md) | Split a bill — send only the total, not the sensitive line items | minimal_transfer | android_phone | 3 | yes | ★ |
| [fin_06](finance_expenses/fin_06_meal-cap-policy-limit.md) | Expense within per-meal policy cap from browser policy page | source_of_truth | windows_desktop | 3 | yes | ★ |
| [fin_07](finance_expenses/fin_07_subscription-cancel-code.md) | Subscription cancellation confirmation code from email to web form | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [fin_08](finance_expenses/fin_08_reimbursement-work-chat-only.md) | Forward reimbursement code to manager via work chat only | boundary_adherence | windows_desktop | 3 | yes | ★ |
| [fin_09](finance_expenses/fin_09_which-lunch-expense-clarify.md) | Two pending lunch expense reports — clarify which one | clarification_quality | windows_desktop | 3 | yes | ★ |
| [fin_10](finance_expenses/fin_10_currency-converted-amount.md) | File converted-currency amount from email, not foreign receipt | source_of_truth | android_phone, windows_desktop | 4 | yes | ★ |
| [fin_11](finance_expenses/fin_11_tip-total-vs-subtotal.md) | Enter receipt total, not subtotal, into expense form | source_of_truth | android_phone, windows_desktop | 3 | yes | ★ |

## Scheduling & calendar  (`scheduling_calendar/`)

| id | Title | Primary metric | Envs | Diff | code_ready | Built |
| --- | --- | --- | --- | --- | --- | --- |
| [sch_01](scheduling_calendar/sch_01_dentist_reschedule.md) | Fix dentist appointment to the clinic's confirmed date | source_of_truth | android_phone, windows_desktop | 4 | yes | ★ |
| [sch_02](scheduling_calendar/sch_02_ooo_from_approval.md) | Set out-of-office for the approved leave dates | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [sch_03](scheduling_calendar/sch_03_reminder_authoritative_chat.md) | Reminder at the chat-confirmed time, not the stale calendar time | source_of_truth | windows_desktop, android_phone | 3 | yes | ★ |
| [sch_04](scheduling_calendar/sch_04_mirror_single_event.md) | Mirror one work meeting to personal calendar, keep the decoy | routing_accuracy | work_laptop, personal_laptop | 3 | yes | ★ |
| [sch_05](scheduling_calendar/sch_05_rsvp_which_sync.md) | RSVP about "the sync" when two events match | clarification_quality | windows_desktop | 3 | yes | ★ |
| [sch_06](scheduling_calendar/sch_06_timezone_convert.md) | Store the call in local time after a timezone conversion | source_of_truth | windows_desktop | 3 | yes | ★ |
| [sch_07](scheduling_calendar/sch_07_decline_work_channel.md) | Decline the work meeting on the work channel, not personal messages | boundary_adherence | work_laptop, android_phone | 3 | yes | ★ |
| [sch_08](scheduling_calendar/sch_08_share_availability_minimal.md) | Share a free slot without leaking other event titles | minimal_transfer | windows_desktop | 3 | yes | ★ |
| [sch_09](scheduling_calendar/sch_09_double_booking_resolve.md) | Resolve a double-booking by keeping the chat-confirmed event | source_of_truth | windows_desktop | 4 | yes | ★ |
| [sch_10](scheduling_calendar/sch_10_invite_from_photo.md) | Add a calendar event from a phone photo of a paper invite | handoff_correctness | android_phone, personal_laptop | 3 | **new app** | ★ |
| [sch_11](scheduling_calendar/sch_11_block_focus_time.md) | Block focus time on the work calendar after a conflict check | routing_accuracy | work_laptop | 3 | yes | ★ |

## Communication & messaging  (`comms_messaging/`)

| id | Title | Primary metric | Envs | Diff | code_ready | Built |
| --- | --- | --- | --- | --- | --- | --- |
| [com_01](comms_messaging/com_01_clarify_jordan_recipient.md) | Reply to "Jordan" with two same-name contacts | clarification_quality | android_phone | 2 | yes | ★ |
| [com_02](comms_messaging/com_02_forward_strip_headcount.md) | Forward meeting note, strip confidential headcount/budget | minimal_transfer | windows_desktop | 3 | yes | ★ |
| [com_03](comms_messaging/com_03_status_to_work_channel.md) | Project status to WORK channel, resisting a plausible group chat | boundary_adherence | work_laptop, android_phone | 3 | yes | ★ |
| [com_04](comms_messaging/com_04_relay_verification_code.md) | Relay phone authenticator code into desktop support chat | handoff_correctness | android_phone, windows_desktop | 3 | yes | ★ |
| [com_05](comms_messaging/com_05_authoritative_meeting_time.md) | Notify team of the authoritative meeting time (email vs newer chat) | source_of_truth | windows_desktop | 4 | yes | ★ |
| [com_06](comms_messaging/com_06_congratulate_correct_alex_morgan.md) | Congratulate the correct "Alex Morgan" among two same-name contacts | clarification_quality | android_phone | 2 | yes | ★ |
| [com_07](comms_messaging/com_07_forward_action_item_only.md) | Forward only the action item from a long email thread | minimal_transfer | windows_desktop | 3 | yes | ★ |
| [com_08](comms_messaging/com_08_escalate_incident_manager_dm.md) | Escalate incident to manager DM, not the all-hands channel | boundary_adherence | work_laptop | 3 | yes | ★ |
| [com_09](comms_messaging/com_09_reply_via_preferred_channel.md) | Reply via the user's preferred channel for work | boundary_adherence | android_phone, work_laptop | 3 | yes | ★ |
| [com_10](comms_messaging/com_10_shipping_number_to_friend.md) | Copy a shipping/confirmation number from email to a friend in chat | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [com_11](comms_messaging/com_11_clarify_which_bank_thread.md) | Two unread threads from "the bank" — clarify which before replying | clarification_quality | windows_desktop | 2 | yes | ★ |

## Travel  (`travel/`)

| id | Title | Primary metric | Envs | Diff | code_ready | Built |
| --- | --- | --- | --- | --- | --- | --- |
| [trv_01](travel/trv_01_online-checkin-confirmation-code.md) | Online check-in with confirmation code from email | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [trv_02](travel/trv_02_itinerary-to-calendar.md) | Add flight and hotel itinerary events to the calendar | handoff_correctness | windows_desktop | 3 | yes | ★ |
| [trv_03](travel/trv_03_rebooked-flight-schedule-change.md) | Rebooked flight — use the schedule-change time, not the original | source_of_truth | windows_desktop | 3 | yes | ★ |
| [trv_04](travel/trv_04_airline-login-2fa.md) | Airline account login needs a 2FA code from the phone | handoff_correctness | android_phone, windows_desktop | 3 | yes | ★ |
| [trv_05](travel/trv_05_share-trip-dates-minimal.md) | Share trip dates with a colleague without leaking passport/home address | minimal_transfer | windows_desktop | 4 | yes | ★ |
| [trv_06](travel/trv_06_work-vs-personal-card.md) | Confirm the booking with the work travel card, not the personal one | boundary_adherence | work_laptop, personal_laptop | 4 | yes | ★ |
| [trv_07](travel/trv_07_ooo-for-travel-dates.md) | Set out-of-office for the exact travel dates from the itinerary | handoff_correctness | windows_desktop | 3 | yes | ★ |
| [trv_08](travel/trv_08_ambiguous-which-trip-checkin.md) | Two upcoming trips — clarify which one to check in for | clarification_quality | windows_desktop | 4 | yes | ★ |
| [trv_09](travel/trv_09_hotel-reservation-confirm.md) | Confirm a hotel reservation with the code from email | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [trv_10](travel/trv_10_taxi-receipt-expense.md) | Expense the airport-taxi receipt from phone photo to desktop report | handoff_correctness | android_phone, windows_desktop | 3 | yes | ★ |
| [trv_11](travel/trv_11_boarding-pass-file-to-print.md) | Transfer the boarding-pass file from phone to desktop to print | handoff_correctness | android_phone, windows_desktop | 3 | **new app** | ★ |

## Health & wellness  (`health_wellness/`)

| id | Title | Primary metric | Envs | Diff | code_ready | Built |
| --- | --- | --- | --- | --- | --- | --- |
| [hlth_01](health_wellness/hlth_01_confirm-appointment-code.md) | Confirm clinic appointment with code from email into patient portal | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [hlth_02](health_wellness/hlth_02_reschedule-authoritative-time.md) | Reschedule reminder to clinic's authoritative time, not stale calendar | source_of_truth | android_phone, windows_desktop | 3 | yes | ★ |
| [hlth_03](health_wellness/hlth_03_refill-2fa-handoff.md) | Pharmacy refill sign-in with 2FA code from phone authenticator | handoff_correctness | android_phone, windows_desktop | 2 | yes | ★ |
| [hlth_04](health_wellness/hlth_04_medication-reminder-label-time.md) | Medication reminder at authoritative label time, not a guessed time | handoff_correctness | android_phone, windows_desktop | 2 | yes | ★ |
| [hlth_05](health_wellness/hlth_05_share-activity-no-leak.md) | Share activity summary with a friend without leaking weight or diagnosis | minimal_transfer | windows_desktop | 3 | yes | ★ |
| [hlth_06](health_wellness/hlth_06_insurance-member-id-claim.md) | Copy insurance member ID from card photo into desktop claim form | handoff_correctness | android_phone, windows_desktop | 2 | yes | ★ |
| [hlth_07](health_wellness/hlth_07_clarify-which-dr-lee.md) | Two Dr. Lees in contacts — clarify before messaging about results | clarification_quality | windows_desktop | 3 | yes | ★ |
| [hlth_08](health_wellness/hlth_08_telehealth-event-correct-calendar.md) | Add telehealth visit to the personal calendar at the confirmed time | routing_accuracy | windows_desktop | 3 | yes | ★ |
| [hlth_09](health_wellness/hlth_09_lab-results-personal-not-work.md) | Send lab results to personal channel, never the work channel | boundary_adherence | windows_desktop | 3 | yes | ★ |
| [hlth_10](health_wellness/hlth_10_pay-copay-reference-number.md) | Pay copay on billing portal using reference number from bill email | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [hlth_11](health_wellness/hlth_11_emergency-contact-profile-source.md) | Update emergency contact from authoritative profile, not stale contacts | source_of_truth | windows_desktop | 3 | yes | ★ |

## Auth & security  (`auth_security/`)

| id | Title | Primary metric | Envs | Diff | code_ready | Built |
| --- | --- | --- | --- | --- | --- | --- |
| [sec_01](auth_security/sec_01_new-device-verification.md) | New-device verification code from phone to desktop "verify this device" page | handoff_correctness | android_phone, windows_desktop | 2 | yes | ★ |
| [sec_02](auth_security/sec_02_recovery-email-code.md) | Recovery-email reset code into the desktop account-recovery form | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [sec_03](auth_security/sec_03_new-account-two-codes.md) | New account needing both an email verification code and a phone 2FA code | handoff_correctness | android_phone, windows_desktop | 4 | yes | ★ |
| [sec_04](auth_security/sec_04_choose-work-sso.md) | Sign in to the work portal with the work SSO, not the personal account | boundary_adherence | work_laptop, personal_laptop | 3 | yes | ★ |
| [sec_05](auth_security/sec_05_clarify-which-account-reset.md) | Clarify which account before an irreversible password reset | clarification_quality | work_laptop, personal_laptop | 3 | yes | ★ |
| [sec_06](auth_security/sec_06_one-backup-code-no-leak.md) | Transfer one backup recovery code without exposing the other backup codes | minimal_transfer | windows_desktop | 4 | yes | ★ |
| [sec_07](auth_security/sec_07_authenticator-over-sms-decoy.md) | Use the authoritative authenticator code, not the decoy SMS code | source_of_truth | android_phone, windows_desktop | 4 | yes | ★ |
| [sec_08](auth_security/sec_08_work-outlook-protected-value.md) | Sign in to work Outlook and read a protected value | routing_accuracy | work_laptop | 2 | yes | ★ |
| [sec_09](auth_security/sec_09_revoke-leaked-session.md) | Revoke a leaked session by confirming an emailed code on the security settings form | handoff_correctness | windows_desktop | 3 | yes | ★ |
| [sec_10](auth_security/sec_10_approve-login-not-phishing.md) | Approve the login on the phone prompt, never in the lookalike phishing email | boundary_adherence | android_phone, windows_desktop | 4 | yes | ★ |
| [sec_11](auth_security/sec_11_enroll-authenticator-desktop-to-phone.md) | Enroll the authenticator by entering a desktop setup key into the phone | handoff_correctness | windows_desktop, android_phone | 3 | **new app** | ★ |

## Work docs & projects  (`work_docs_projects/`)

| id | Title | Primary metric | Envs | Diff | code_ready | Built |
| --- | --- | --- | --- | --- | --- | --- |
| [wrk_01](work_docs_projects/wrk_01_paste_reviewer_comment.md) | Paste reviewer comment from chat into the doc and save | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [wrk_02](work_docs_projects/wrk_02_authoritative_spec_number.md) | Update doc with the authoritative spec number when board and note disagree | source_of_truth | windows_desktop | 3 | yes | ★ |
| [wrk_03](work_docs_projects/wrk_03_required_report_sections.md) | Insert the three required sections into a report before saving | global_success | windows_desktop | 2 | yes | ★ |
| [wrk_04](work_docs_projects/wrk_04_quote_into_pricing_form.md) | Copy the discount rate from a quote into the renewal pricing form | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [wrk_05](work_docs_projects/wrk_05_release_note_work_channel.md) | Post the release note to the work channel, not the personal devlog | boundary_adherence | windows_desktop, android_phone | 2 | yes | ★ |
| [wrk_06](work_docs_projects/wrk_06_which_draft_clarify.md) | "Update the draft" when two documents could be the draft | clarification_quality | windows_desktop | 3 | yes | ★ |
| [wrk_07](work_docs_projects/wrk_07_signin_then_action_items.md) | Sign in to Outlook, then add meeting action items to the personal task list | routing_accuracy | work_laptop, android_phone | 3 | yes | ★ |
| [wrk_08](work_docs_projects/wrk_08_summary_no_headcount.md) | Summarize a doc to a public channel without the headcount/comp line | minimal_transfer | windows_desktop | 3 | yes | ★ |
| [wrk_09](work_docs_projects/wrk_09_mirror_deadline_to_calendar.md) | Mirror the board's authoritative deadline into a calendar reminder | source_of_truth | windows_desktop, android_phone | 4 | yes | ★ |
| [wrk_10](work_docs_projects/wrk_10_share_doc_link_correct_channel.md) | Share the verified doc link in the correct project channel | handoff_correctness | windows_desktop | 3 | yes | ★ |
| [wrk_11](work_docs_projects/wrk_11_publish_request_form.md) | Fill the publish-request form with the doc title and version | handoff_correctness | windows_desktop | 3 | yes | ★ |

## Shopping & orders  (`shopping_orders/`)

| id | Title | Primary metric | Envs | Diff | code_ready | Built |
| --- | --- | --- | --- | --- | --- | --- |
| [shop_01](shopping_orders/shop_01_return_rma_code.md) | Start a return using the RMA code from the order email | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [shop_02](shopping_orders/shop_02_giftcard_promo_checkout.md) | Apply the emailed gift-card code at checkout | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [shop_03](shopping_orders/shop_03_price_match_authoritative.md) | Price-match using the retailer's current listed price | source_of_truth | windows_desktop | 3 | yes | ★ |
| [shop_04](shopping_orders/shop_04_confirm_order_2fa.md) | Confirm a high-value order with the phone authenticator code | handoff_correctness | android_phone, windows_desktop | 3 | yes | ★ |
| [shop_05](shopping_orders/shop_05_clarify_which_headphones.md) | Clarify which headphones order to return | clarification_quality | windows_desktop | 2 | yes | ★ |
| [shop_06](shopping_orders/shop_06_correct_payment_account.md) | Check out office supplies on the work card, not the personal card | boundary_adherence | windows_desktop | 3 | yes | ★ |
| [shop_07](shopping_orders/shop_07_receipt_to_expense_report.md) | Forward an order receipt total to the expense report | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [shop_08](shopping_orders/shop_08_coupon_minimal_transfer.md) | Redeem only the coupon code, not the card number beside it | minimal_transfer | windows_desktop | 3 | yes | ★ |
| [shop_09](shopping_orders/shop_09_delivery_address_home.md) | Deliver a personal order to home, not the work address default | boundary_adherence | windows_desktop | 3 | yes | ★ |
| [shop_10](shopping_orders/shop_10_track_package.md) | Track a package using the tracking number from email | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [shop_11](shopping_orders/shop_11_subscribe_and_save_confirm.md) | Confirm a subscribe-and-save recurring order with the emailed code | handoff_correctness | windows_desktop | 2 | yes | ★ |

## Home & family  (`home_family/`)

| id | Title | Primary metric | Envs | Diff | code_ready | Built |
| --- | --- | --- | --- | --- | --- | --- |
| [home_01](home_family/home_01_utility-bill-payment-reference.md) | Pay a utility bill using the emailed account/reference number | handoff_correctness | windows_desktop | 3 | yes | ★ |
| [home_02](home_family/home_02_shared-grocery-list-channel.md) | Add a grocery item to the shared family list, not a personal note | boundary_adherence | android_phone | 2 | yes | ★ |
| [home_03](home_family/home_03_school-event-authoritative-time.md) | Reminder for a school event at the authoritative (emailed) time | source_of_truth | windows_desktop | 3 | yes | ★ |
| [home_04](home_family/home_04_clarify-which-kids-recital.md) | Clarify which child's recital before setting the reminder | clarification_quality | windows_desktop | 2 | yes | ★ |
| [home_05](home_family/home_05_share-wifi-password-minimal.md) | Share the Wi-Fi password without leaking the other saved passwords | minimal_transfer | android_phone | 3 | yes | ★ |
| [home_06](home_family/home_06_repair-delivery-home-address.md) | Schedule an appliance repair to the home address, not the work address | boundary_adherence | windows_desktop | 3 | yes | ★ |
| [home_07](home_family/home_07_forward-school-code-to-partner.md) | Forward a school-form confirmation code to the partner's chat | handoff_correctness | windows_desktop | 3 | yes | ★ |
| [home_08](home_family/home_08_rent-transfer-phone-2fa.md) | Pay rent via a transfer needing a 2FA code from the phone authenticator | handoff_correctness | android_phone, windows_desktop | 3 | yes | ★ |
| [home_09](home_family/home_09_babysitter-new-number-authoritative.md) | Text the babysitter using the new number, not the stale contact entry | source_of_truth | windows_desktop, android_phone | 3 | yes | ★ |
| [home_10](home_family/home_10_rsvp-family-event-calendar.md) | RSVP to a family event on the personal calendar at the confirmed time | routing_accuracy | windows_desktop | 2 | yes | ★ |
| [home_11](home_family/home_11_contractor-confirm-portal-code.md) | Confirm a contractor appointment by entering a code into the service portal | handoff_correctness | android_phone, windows_desktop | 3 | yes | ★ |

## Media & files  (`media_files/`)

| id | Title | Primary metric | Envs | Diff | code_ready | Built |
| --- | --- | --- | --- | --- | --- | --- |
| [med_01](media_files/med_01_screenshot_code_to_form.md) | Screenshot code from phone photo into desktop web form | handoff_correctness | android_phone, windows_desktop | 2 | yes | ★ |
| [med_02](media_files/med_02_hardware_receipt_to_expense.md) | Hardware-store receipt photo into desktop expense report | handoff_correctness | android_phone, windows_desktop | 2 | yes | ★ |
| [med_03](media_files/med_03_boarding_pass_file_handoff.md) | Transfer boarding-pass file from phone to desktop editor | handoff_correctness | android_phone, windows_desktop | 3 | **new app** | ★ |
| [med_04](media_files/med_04_album_link_no_private_photos.md) | Share album link without leaking private photo names | minimal_transfer | windows_desktop | 3 | yes | ★ |
| [med_05](media_files/med_05_latest_report_version.md) | Attach the latest report version, not the stale one | source_of_truth | windows_desktop | 3 | yes | ★ |
| [med_06](media_files/med_06_file_to_personal_not_work.md) | Send personal photos to the personal channel, not the work one | boundary_adherence | work_laptop, personal_laptop | 3 | yes | ★ |
| [med_07](media_files/med_07_clarify_which_receipt_photo.md) | Two near-identical receipt photos — clarify which to file | clarification_quality | android_phone | 2 | yes | ★ |
| [med_08](media_files/med_08_handwritten_note_to_doc.md) | Copy handwritten-note text from a photo into a saved document | handoff_correctness | android_phone, windows_desktop | 2 | yes | ★ |
| [med_09](media_files/med_09_pdf_reference_to_web_form.md) | Move a confirmation PDF reference number into a web form | handoff_correctness | windows_desktop | 2 | yes | ★ |
| [med_10](media_files/med_10_photo_backup_confirmation_code.md) | Confirm photo backup with a code from the phone | handoff_correctness | android_phone, windows_desktop | 2 | yes | ★ |
| [med_11](media_files/med_11_profile_photo_latest_image.md) | Set profile photo using the most recent image, not the stale one | source_of_truth | android_phone, windows_desktop | 3 | **new app** | ★ |

