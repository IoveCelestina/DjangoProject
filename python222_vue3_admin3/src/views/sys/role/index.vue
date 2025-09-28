<template>
	<div class="app-container">
		<el-row :gutter="20" class="header">
			<el-col :span="7">
				<el-input placeholder="请输入角色名..." v-model="queryForm.query"
						  clearable></el-input>
			</el-col>
			<el-button type="primary" :icon="Search" @click="initRoleList">搜索</el-button>
				<el-button type="success" :icon="DocumentAdd"
						   @click="handleDialogValue()">新增</el-button>
				<el-popconfirm title="您确定批量删除这些记录吗？"
							   @confirm="handleDelete(null)">
					<template #reference>
						<el-button type="danger" :disabled="delBtnStatus" :icon="Delete">批量删
							除</el-button>
					</template>
				</el-popconfirm>
		</el-row>
		<el-table
			:data="tableData"
			stripe
			style="width: 100%"
			@selection-change="handleSelectionChange">
			<el-table-column type="selection" width="55"/>
			<el-table-column prop="name" label="角色名" width="100" align="center"/>
			<el-table-column prop="code" label="权限字符" width="200" align="center"/>
			<el-table-column prop="create_time" label="创建时间" width="200"
							 align="center"/>
			<el-table-column prop="remark" label="备注"/>
			<el-table-column prop="action" label="操作" width="400" fixed="right"
							 align="center">
				<template v-slot="scope">
					<el-button type="primary" :icon="Tools"
							   @click="handleMenuDialogValue(scope.row.id)">分配权限</el-button>
					<el-button v-if="scope.row.code!='admin'" type="primary" :icon="Edit"
							   @click="handleDialogValue(scope.row.id)"/>
					<el-popconfirm v-if="scope.row.code!='admin'" title="您确定要删除这条记录
吗？" @confirm="handleDelete(scope.row.id)">
						<template #reference>
							<el-button type="danger" :icon="Delete"/>
						</template>
					</el-popconfirm>
				</template>
			</el-table-column>
		</el-table>
		<el-pagination
			v-model:currentPage="queryForm.pageNum"
			v-model:page-size="queryForm.pageSize"
			:page-sizes="[10, 20, 30, 40,50]"
			layout="total, sizes, prev, pager, next, jumper"
			:total="total"
			@size-change="handleSizeChange"
			@current-change="handleCurrentChange"
		/>
	</div>
</template>
<script setup>
import {Search, Delete, DocumentAdd, Edit, Tools, RefreshRight} from '@element-plus/icons-vue'
import {ref} from 'vue'
import requestUtil, {getServerUrl} from "@/util/request";
import {ElMessage, ElMessageBox} from 'element-plus'
const queryForm = ref({
	query: '',
	pageNum: 1,
	pageSize: 10
})
const total = ref(0)
const tableData = ref([])
const initRoleList = async () => {
	const res = await requestUtil.post("role/search", queryForm.value)
	tableData.value = res.data.roleList;
	total.value = res.data.total;
}
initRoleList();
const handleSizeChange = (pageSize) => {
	queryForm.value.pageNum = 1;
	queryForm.value.pageSize = pageSize;
	initRoleList();
}
const handleCurrentChange = (pageNum) => {
	queryForm.value.pageNum = pageNum;
	initRoleList();
}
</script>
<style lang="scss" scoped>
.header {
	padding-bottom: 16px;
	box-sizing: border-box;
}
.el-pagination {
	float: right;
	padding: 20px;
	box-sizing: border-box;
}
::v-deep th.el-table__cell {
	word-break: break-word;
	background-color: #f8f8f9 !important;
	color: #515a6e;
	height: 40px;
	font-size: 13px;
}
.el-tag--small {
	margin-left: 5px;
}
</style>