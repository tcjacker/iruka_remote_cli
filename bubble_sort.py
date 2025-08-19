def bubble_sort(arr):
    """
    使用冒泡排序算法对列表进行升序排序。

    参数:
    arr (list): 需要排序的数字列表。

    返回:
    list: 排序后的列表。
    """
    n = len(arr)
    # 遍历所有数组元素
    for i in range(n):
        # 设置一个标志，如果在一轮内没有发生交换，说明列表已经有序
        swapped = False
        # 最后一轮的i个元素已经排好序，所以内层循环可以减少比较次数
        for j in range(0, n - i - 1):
            # 遍历数组从0到n-i-1
            # 如果找到的元素大于下一个元素，则交换它们
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        
        # 如果在一轮完整的内层循环中没有发生任何交换，则数组已经排序完成
        if not swapped:
            break
    return arr

# --- 示例 ---
if __name__ == "__main__":
    my_list = [64, 34, 25, 12, 22, 11, 90]
    print(f"原始列表: {my_list}")
    
    sorted_list = bubble_sort(my_list)
    print(f"排序后的列表: {sorted_list}")

    # --- 另一个例子 ---
    another_list = [5, 1, 4, 2, 8]
    print(f"\n原始列表: {another_list}")
    sorted_list_2 = bubble_sort(another_list)
    print(f"排序后的列表: {sorted_list_2}")
