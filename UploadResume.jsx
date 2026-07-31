function UploadResume(){

return(
<div className="bg-gray-900 p-10 rounded-3xl">

<h2 className="text-2xl font-semibold mb-5">
Upload your resume
</h2>


<input 
type="file"
className="border p-3 rounded"
/>


<button className="mt-5 bg-blue-600 px-6 py-3 rounded-xl">
Analyze Resume
</button>


</div>
)

}

export default UploadResume;