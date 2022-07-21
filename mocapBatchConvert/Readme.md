## How To Use

1. Create [templateName] hooks under folder hooks

2. Create [templateName] yaml under folder yaml

3. Change [templateName] in main.py

4. Run
```
import sys

sys.path.append(r'I:\script\bin\td\maya\scripts\mocapConvert\mocapBatchConvert\generateSkeleton')

import mocap_matchmaker
reload(mocap_matchmaker)

mocap_matchmaker.run()
```
To Export Skeleton Fbx

5. batch convert
import sys
sys.path.append(r"I:\script\bin\td\maya\scripts\mocapConvert\mocapBatchConvert")
import main
reload(main)
main.main()