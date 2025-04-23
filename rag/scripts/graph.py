import matplotlib.pyplot as plt

alpha_values = [
    0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 
    0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0
]
recall_at_1 = [
    0.53, 0.55, 0.57, 0.61, 0.63, 0.63, 0.67, 0.74, 0.77, 0.79, 
    0.80, 0.83, 0.82, 0.80, 0.79, 0.79, 0.79, 0.80, 0.78, 0.76, 0.75
]
in_context = [
    0.73, 0.80, 0.76, 0.78, 0.81, 0.83, 0.84, 0.84, 0.92, 0.93, 
    0.94, 0.96, 0.96, 0.94, 0.94, 0.95, 0.94, 0.95, 0.95, 0.92, 0.91
]

max_idx = recall_at_1.index(max(recall_at_1))
optimal_alpha = alpha_values[max_idx]
optimal_score = recall_at_1[max_idx]

plt.figure(figsize=(10, 5), dpi=300)
plt.plot(alpha_values, in_context, marker='o', linestyle='-', label='Recall@k')
plt.plot(alpha_values, recall_at_1, marker='o', linestyle='-', label='Recall@1')

plt.xlabel(r'$\alpha$', fontsize=12)
plt.ylabel('Score', fontsize=12)
plt.xticks([i / 10.0 for i in range(0, 11)])
plt.yticks([i / 10.0 for i in range(0, 11)])
plt.ylim(0, 1)

plt.text(-0.01, -0.08, 'keyword', ha='center', va='center', fontsize=10, transform=plt.gca().transData)
plt.text(1.01, -0.08, 'vector', ha='center', va='center', fontsize=10, transform=plt.gca().transData)

plt.grid(True, which='both', color='lightgray', linestyle='--', linewidth=0.5)
plt.legend(fontsize=10)
plt.tight_layout()

plt.savefig("alpha_recall.pdf", format='pdf')
# plt.show()