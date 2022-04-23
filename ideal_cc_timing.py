# Number of scvs at which to add on bases
scvs = [ 16 + 2*3 + 7, 2*16 + 4*3-1, 3*16 + 6*3+1 ]
def num_bases(num_scvs):
    global scvs
    num_base = 1
    for i in scvs:
        if num_scvs >= i:
            num_base = num_base + 1
    return num_base
    

def timer_string(timer_seconds):
    timer_seconds = int(timer_seconds)
    if timer_seconds>0:
        return str(timer_seconds//60).zfill(2) + ":" + str(timer_seconds%60).zfill(2)
    else:
        return "99:99"

# one tick is 12 seconds
# 92s for CC to construct
scv_count = [12]

while(scv_count[-1] < 88):
    scv_count.append(scv_count[-1]+num_bases(scv_count[-1]))

print(scv_count)

saturation_index = []
for x in scvs:
    saturation_index.append(scv_count.index(x))
saturation_index.append(len(scv_count)-1)

for i in saturation_index:
    print(str(scv_count[i]) + " " + timer_string(12*i - 96) + " " + timer_string(12*i))