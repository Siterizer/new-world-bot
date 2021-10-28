import threading

import utils.global_variables as gv
import keyboard
from functionality.fishing_actions import *
from functionality.image_recognition import image_recognition_result
from wrappers.logging_wrapper import info, debug
from utils.config import dict, random_timeout
from time import time
from functools import partial
from datetime import datetime

def fishing_loop(event):
    if(gv.loop_count == 500):
        threading.Thread(target=fishing_loop, args=(event,)).start()
        gv.loop_count = 0
        return

    if (not gv.continue_fishing):
        info('stopping loop')
        return

    gv.total_minutes = math.floor((datetime.now() - gv.start_time).total_seconds() / 60.0)
    gv.minutes_text_label["text"] = "Time (minutes): " + str(gv.total_minutes)
    gv.loop_count+=1
    info('starting new loop ' + str(gv.loop_count))
    gv.last_results.add(call_appropriate_fishing_action(event))
    if(gv.last_results.is_full_of('0')):
        if(dict['repairing']['enable'].get() == 1):
            should_repair_in = -1 * (int(time()) - gv.last_repair_time - dict['repairing']['every'].get())
            debug("Repair in: " + str(should_repair_in))
            if(should_repair_in < 0):
                gv.last_repair_time = int(time())
                info("Repairing")
                repairing(event)
                if dict['bait']['enable'].get():
                    info("Selecting bait")
                    select_bait(event)
    if (gv.continue_fishing):
        gv.root.after(int(random_timeout(dict['fishing']['timeouts']['loop'])*1000), fishing_loop(event))


def call_appropriate_fishing_action(event):
    result_from_model = image_recognition_result(dict['fishing']['x'].get(), dict['fishing']['y'].get(),
                                         dict['fishing']['width'].get(), dict['fishing']['height'].get())

    if(gv.last_results.get_last_value() != result_from_model and result_from_model != '1'): # double checking that it is a correct match
        return result_from_model
    if result_from_model == '0': # 0 - model does not match any data (not fish captured yet)
        if(gv.last_results.get_one_before_last_value() != '0'):
            info("Waiting for fish...")
        return '0'
    elif result_from_model == '1': # 1 - model noticed a fish(left click to initiate fishing)
        info("Found a fish!")
        gv.total_found += 1
        gv.found_text_label["text"] = "Found: " + str(gv.total_found)
        fish_notice(event)
        return '1'
    elif result_from_model == '2': #2 - model matched the green icon (reeling a fish in)
        info("Green color spotted, Reeling a fish")
        gv.last_detected_green_before_casting = True
        reel_fish(event)
        return '2'
    elif result_from_model == '3': #3 - model matched the orange icon (wait x sec)
        if(gv.last_results.are_too_much_pauses()):
            info("Too much pauses, Reeling a fish!")
            reel_fish(event)
            return '3'
        info("Orange color spotted, Pause fishing")
        pause(event)
        return '3'
    elif result_from_model == '4': #4 - model matched the red icon (wait x sec)
        info("Red color spotted, Pause fishing")
        pause(event)
        return '4'
    elif result_from_model == '5': #5 - model did not match anything (left click, wait x sec)
        if (gv.last_detected_green_before_casting):
            # press left click to exit animation
            info("Caught a fish!")
            gv.total_caught += 1
            gv.caught_text_label["text"] = "Caught: " + str(gv.total_caught)
            gv.last_detected_green_before_casting = False
        info("Cast fishing rod")
        gv.total_casts += 1
        gv.casts_text_label["text"] =  "Casts: " + str(gv.total_casts)
        cast(event)
        return '5'
