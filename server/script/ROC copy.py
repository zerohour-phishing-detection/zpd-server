import sqlite3

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import roc_curve, roc_auc_score, make_scorer, accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split, KFold, cross_val_score, cross_validate, StratifiedKFold
import matplotlib.pyplot as plt
import joblib

import warnings
warnings.filterwarnings("ignore")

# DB handles
conn_p = sqlite3.connect('db/storage.phishing-copy.db')
curs_p = conn_p.cursor();

conn_b = sqlite3.connect('db/storage.benign-copy.db')
curs_b = conn_b.cursor();

def effect(labeln, field, fielddelim, perfectval):
	# Filter Settings
	pfilter = "region_info.dominant_colour_pct > 9 and region_info.dominant_colour_pct < 76 and region_info.colourcount > 30 and region_info.colourcount < 8572 and region_info.width*region_info.height < 29071 and region_info.width*region_info.height > 782 and region_info.xcoord > 50 and region_info.xcoord < 1000 and region_info.ycoord > 10 and region_info.ycoord < 750"

	# files to save best models to
	text_clf = f"{labeln}-clf_t.joblib"
	img_clf = f"{labeln}-clf_i.joblib"
	comb_clf = f"{labeln}-clf_b.joblib"


	# storage var's
	dataX_text = np.array([])
	dataY_text = np.array([])
	
	dataX_image = np.array([])
	dataY_image = np.array([])
	
	dataX_both = np.array([])
	dataY_both = np.array([])
	# Phishing Data		
	sqlq = f"select distinct {field}, filepath from search_result_text where {fielddelim} <> '' group by filepath"
	results = curs_p.execute(sqlq).fetchall()
	for row in results:
		dataX_text = np.append(dataX_text, row[0])
		dataY_text = np.append(dataY_text, 1)
		
	sqlq = f"select distinct {field}, search_result_image.filepath as filepath  from search_result_image, region_info where search_result_image.filepath = region_info.filepath and search_result_image.region = region_info.region and {fielddelim} <> '' group by search_result_image.filepath"
	results = curs_p.execute(sqlq).fetchall()
	for row in results:
		dataX_image = np.append(dataX_image, row[0])
		dataY_image = np.append(dataY_image, 1)
		
	sqlq = f"select distinct {field}, search_result_image.filepath as filepath  from search_result_image, region_info where search_result_image.filepath = region_info.filepath and search_result_image.region = region_info.region and {fielddelim} <> '' union select distinct {field}, filepath from search_result_text where {fielddelim} <> '' group by filepath"
	results = curs_p.execute(sqlq).fetchall()
	for row in results:
		dataX_both = np.append(dataX_both, row[0])
		dataY_both = np.append(dataY_both, 1)

	# Benign Data - of the ones we still need to test		
	sqls = f"select distinct {field}, filepath from search_result_text  where {fielddelim} <> '' and filepath not in (select distinct filepath from search_result_text where hit <> '') group by filepath"
	results = curs_b.execute(sqls).fetchall()
	for row in results:
		dataX_text = np.append(dataX_text, row[0])
		dataY_text = np.append(dataY_text, 0)
		
	sqls = f"select distinct {field}, search_result_image.filepath as filepath  from search_result_image, region_info where search_result_image.filepath = region_info.filepath and search_result_image.region = region_info.region and {fielddelim} <> '' and region_info.filepath not in (select distinct filepath from search_result_image where hit <> '') group by search_result_image.filepath"
	results = curs_b.execute(sqls).fetchall()
	for row in results:
		dataX_image = np.append(dataX_image, row[0])
		dataY_image = np.append(dataY_image, 0)
		
	sqls = f"select distinct {field}, search_result_image.filepath as filepath  from search_result_image, region_info where search_result_image.filepath = region_info.filepath and search_result_image.region = region_info.region and {fielddelim} <> '' and region_info.filepath not in (select distinct filepath from search_result_text where hit <> '' union select distinct filepath from search_result_image where hit <> '') union select distinct {field}, filepath from search_result_text  where {fielddelim} <> '' and filepath not in (select distinct filepath from search_result_text where hit <> '' union select distinct filepath from search_result_image where hit <> '') group by filepath"
	results = curs_b.execute(sqls).fetchall()
	for row in results:
		dataX_both = np.append(dataX_both, row[0])
		dataY_both = np.append(dataY_both, 0)
	
	# Have to resize dataX_both before usage
	#dataX_text = dataX_text.reshape((-1, 1))
	#dataX_image = dataX_image.reshape((-1, 1))
	#dataX_both = dataX_both.reshape((-1, 1))
	#or use dataframe
	dataframeX_text = pd.DataFrame({'fieldval':dataX_text})
	dataframeX_image = pd.DataFrame({'fieldval':dataX_image})
	dataframeX_both = pd.DataFrame({'fieldval':dataX_both})
	
	# Data Splitting
	auc1 = 0.0
	auc2 = 0.0
	auc3 = 0.0
	
	model_t = None
	model_i = None
	model_b = None
	
	data_x_text = None
	data_y_text = None
	
	data_x_image = None
	data_y_image = None
	
	data_x_both = None
	data_y_both = None
	threshold_test = None

	for lp in range(100):
		X_train_text, X_test_text, y_train_text, y_test_text = train_test_split(dataframeX_text, dataY_text, test_size=0.2, stratify=dataY_text)
		clf_dt_text = DecisionTreeClassifier(max_depth=1)
		clf_dt_text.fit(X_train_text, y_train_text)
		y_score1 = clf_dt_text.predict_proba(X_test_text)[:,1]
		false_positive_rate, true_positive_rate, threshold = roc_curve(y_test_text, y_score1)
		sc = roc_auc_score(y_test_text, y_score1)
		if sc > auc1:
			auc1 = sc
			false_positive_rate1 = false_positive_rate
			true_positive_rate1 = true_positive_rate
			model_t = clf_dt_text
			data_x_text = X_test_text
			data_y_text = y_test_text

		X_train_image, X_test_image, y_train_image, y_test_image = train_test_split(dataframeX_image, dataY_image, test_size=0.2, stratify=dataY_image)
		clf_dt_image = DecisionTreeClassifier(max_depth=1)
		clf_dt_image.fit(X_train_image, y_train_image)
		y_score2 = clf_dt_image.predict_proba(X_test_image)[:,1]
		false_positive_rate, true_positive_rate, threshold = roc_curve(y_test_image, y_score2)
		sc = roc_auc_score(y_test_image, y_score2)
		if sc > auc2:
			auc2 = sc
			false_positive_rate2 = false_positive_rate
			true_positive_rate2 = true_positive_rate
			model_i = clf_dt_image
			data_x_image = X_test_image
			data_y_image = y_test_image
		
		
		X_train_both, X_test_both, y_train_both, y_test_both = train_test_split(dataframeX_both, dataY_both, test_size=0.2, stratify=dataY_both)
		clf_dt_both = DecisionTreeClassifier(max_depth=1)
		clf_dt_both.fit(X_train_both, y_train_both)
		y_score3 = clf_dt_both.predict_proba(X_test_both)[:,1]
		false_positive_rate, true_positive_rate, threshold = roc_curve(y_test_both, y_score3)
		sc = roc_auc_score(y_test_both, y_score3)
		if sc > auc3:
			auc3 = sc
			false_positive_rate3 = false_positive_rate
			true_positive_rate3 = true_positive_rate
			model_b = clf_dt_both
			data_x_both = X_test_both
			data_y_both = y_test_both
			threshold_test = threshold[np.argmax(true_positive_rate3 - false_positive_rate3)]
	
	plt.subplot(1,3,1)
	plt.plot(false_positive_rate1, true_positive_rate1, label=f"{labeln}")
	plt.subplot(1,3,2)
	plt.plot(false_positive_rate2, true_positive_rate2, label=f"{labeln}")
	plt.subplot(1,3,3)
	plt.plot(false_positive_rate3, true_positive_rate3, label=f"{labeln}")
	
	scoring = {'accuracy' : make_scorer(accuracy_score), 
			   'precision' : make_scorer(precision_score),
			   'recall' : make_scorer(recall_score), 
			   'f1_score' : make_scorer(f1_score), 
			   'roc_auc' : make_scorer(roc_auc_score)}
	kfold = StratifiedKFold(n_splits=5)
	
	resultsT = cross_validate(model_t, data_x_text, data_y_text, cv=kfold, scoring=scoring)
	resultsI = cross_validate(model_i, data_x_image, data_y_image, cv=kfold, scoring=scoring)
	resultsB = cross_validate(model_b, data_x_both, data_y_both, cv=kfold, scoring=scoring)
	
	print(f"{labeln} & {resultsT['test_accuracy'].mean():.4f} & {resultsT['test_precision'].mean():.4f} &  {resultsT['test_f1_score'].mean():.4f} & {resultsT['test_roc_auc'].mean():.4f} & {resultsI['test_accuracy'].mean():.4f} & {resultsI['test_precision'].mean():.4f} & {resultsI['test_f1_score'].mean():.4f} & {resultsI['test_roc_auc'].mean():.4f} & {resultsB['test_accuracy'].mean():.4f} & {resultsB['test_precision'].mean():.4f} & {resultsB['test_f1_score'].mean():.4f} & {resultsB['test_roc_auc'].mean():.4f}\\\\")

	# save models
	joblib.dump(model_t, text_clf)
	joblib.dump(model_i, img_clf)
	joblib.dump(model_b, comb_clf)

	print(threshold_test)
	
	
	return model_t, model_i, model_b, data_x_text, data_y_text, data_x_image, data_y_image, data_x_both, data_y_both

plt.figure(figsize=(15,5))

plt.subplot(1,3,1)
plt.title('Text Only')
plt.plot([0, 1], ls="--")
plt.plot([0, 0], [1, 0] , c=".7"), plt.plot([1, 1] , c=".7")
plt.ylabel('True Positive Rate')
plt.xlabel('False Positive Rate')

plt.subplot(1,3,2)
plt.title('Image Only')
plt.plot([0, 1], ls="--")
plt.plot([0, 0], [1, 0] , c=".7"), plt.plot([1, 1] , c=".7")
plt.ylabel('True Positive Rate')
plt.xlabel('False Positive Rate')

plt.subplot(1,3,3)
plt.title('Combined')
plt.plot([0, 1], ls="--")
plt.plot([0, 0], [1, 0] , c=".7"), plt.plot([1, 1] , c=".7")
plt.ylabel('True Positive Rate')
plt.xlabel('False Positive Rate')

print("\\textbf{Classifier} & \\textbf{Acc.} & \\textbf{Prec.} & \\textbf{f$_1$} & \\textbf{auc}& \\textbf{Acc.} & \\textbf{Prec.} &\\textbf{f$_1$} & \\textbf{auc}& \\textbf{Acc.} & \\textbf{Prec.} & \\textbf{f$_1$} & \\textbf{auc}  \\\\")
print("\\midrule")

effect("EMD", "min(emd)", "emd", 1.0)
#effect("EMD", "max(emd)", "emd", 1.0)
effect("DCT", "min(dct)", "dct", 1.0)
#effect("DCT", "max(dct)", "dct", 1.0)
effect("PSIM", "min(pixel_sim)", "pixel_sim", 1.0)
#effect("PSIM", "max(pixel_sim)", "pixel_sim", 1.0)
effect("SSIM", "max(structural_sim)", "structural_sim", 0.0)
#effect("SSIM", "max(structural_sim)", "structural_sim", 1.0)
effect("ORB", "max(orb)", "orb", 0.0)
#effect("ORB", "max(orb)", "orb", 1.0)

plt.subplot(1,3,1)
plt.legend()

plt.subplot(1,3,2)
plt.legend()

plt.subplot(1,3,3)
plt.legend()

plt.show()