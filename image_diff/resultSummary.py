# -*- coding: utf-8 -*-


if __name__ == "__main__":

    TP = 442
    TN = 103
    FP = 4
    FN = 14
    print("total=%d,TP=%d,TN=%d,FP=%d,FN=%d"%((TP+TN+FP+FN), TP, TN, FP, FN))
    
    accuracy = (TP+TN)*1.0/(TP+FN+TN+FP)
    precision = (TP)*1.0/(TP+FP)
    recall = (TP)*1.0/(TP+FN)
    f1_score = 2.0*(precision*recall)/(precision+recall)
    print("accuracy=%f%%"%(accuracy*100))
    print("precision=%f%%"%(precision*100))
    print("recall=%f%%"%(recall*100))
    print("f1_score=%f%%"%(f1_score*100))
    
    
    TP = 420
    TN = 124
    FP = 5
    FN = 14
    print("total=%d,TP=%d,TN=%d,FP=%d,FN=%d"%((TP+TN+FP+FN), TP, TN, FP, FN))
    
    accuracy = (TP+TN)*1.0/(TP+FN+TN+FP)
    precision = (TP)*1.0/(TP+FP)
    recall = (TP)*1.0/(TP+FN)
    f1_score = 2.0*(precision*recall)/(precision+recall)
    print("accuracy=%f%%"%(accuracy*100))
    print("precision=%f%%"%(precision*100))
    print("recall=%f%%"%(recall*100))
    print("f1_score=%f%%"%(f1_score*100))