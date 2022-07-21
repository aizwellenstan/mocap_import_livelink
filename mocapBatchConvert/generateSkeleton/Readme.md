import sys

sys.path.append(r'I:\script\bin\td\maya\scripts\mocapConvert\mocapBatchConvert\generateSkeleton')

import mocap_matchmaker
reload(mocap_matchmaker)

mocap_matchmaker.run()